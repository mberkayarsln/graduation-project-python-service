"""Servis Rota Optimizasyon"""
from config import Config
from models.service_planner import ServicePlanner


def main():
    config = Config()
    planner = ServicePlanner(config)
    planner.run()


if __name__ == "__main__":
    main()
