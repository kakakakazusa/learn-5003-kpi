# -*- coding: utf-8 -*-
"""Flask 应用工厂。

模块职责拆分：
- extensions.py  : db 实例
- dw_models.py   : 数仓库（dw bind）模型
- routes/        : 各业务蓝图
"""
import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError

from extensions import db

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-secret")

    dw_database_uri = os.getenv(
        "DW_DATABASE_URL",
        "mysql+pymysql://root:root@127.0.0.1:3306/5003?charset=utf8mb4",
    )
    app.config["SQLALCHEMY_BINDS"] = {"dw": dw_database_uri}

    # 全部模型都在 dw bind（见 dw_models.BaseDW）；默认 bind 仅作占位，
    # 未配置 DATABASE_URL 时直接与数仓库同源，不再需要额外的业务库。
    database_uri = os.getenv("DATABASE_URL") or dw_database_uri
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if database_uri.startswith("mysql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

    origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})
    db.init_app(app)

    # 注册模型与蓝图
    import dw_models  # noqa: F401
    from routes.dw import dw_bp

    app.register_blueprint(dw_bp)

    @app.cli.command("init-db")
    def init_db():
        """Create tables for all configured databases."""
        db.create_all()
        url = db.engine.url
        print(f"Database tables ready: {url.get_backend_name()}/{url.database}")

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.error("Database request failed: %s", error)
        db.session.rollback()
        return jsonify(code=503, message="数据库暂不可用，请检查连接配置和表结构", data=None), 503

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(code=404, message="Not Found", data=None), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify(code=500, message="Internal Server Error", data=None), 500

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    create_app().run(host="127.0.0.1", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
