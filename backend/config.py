import os
from dataclasses import dataclass


@dataclass
class Config:
    # Basic toggles
    vpn_enabled: bool = True
    vpn_endpoint: str = ""
    # Poster storage
    posters_dir: str = "posters"
    # Scraping
    batch_size: int = 10
    max_batches: int = 0  # 0 means no hard cap
    # API
    api_host: str = "127.0.0.1"
    api_port: int = 3000


def _to_bool(v: str) -> bool:
    return str(v).lower() in ("1", "true", "yes", "on")


def load_config() -> Config:
    cfg = Config()
    cfg.vpn_enabled = _to_bool(os.environ.get("VPN_ENABLED", str(cfg.vpn_enabled)))
    cfg.vpn_endpoint = os.environ.get("VPN_ENDPOINT", cfg.vpn_endpoint)
    cfg.posters_dir = os.environ.get("POSTERS_DIR", cfg.posters_dir)
    try:
        cfg.batch_size = int(os.environ.get("SCRAPE_BATCH_SIZE", cfg.batch_size))
    except (TypeError, ValueError):
        pass
    try:
        cfg.max_batches = int(os.environ.get("SCRAPE_MAX_BATCHES", cfg.max_batches))
    except (TypeError, ValueError):
        pass
    cfg.api_host = os.environ.get("API_HOST", cfg.api_host)
    try:
        cfg.api_port = int(os.environ.get("API_PORT", cfg.api_port))
    except (TypeError, ValueError):
        pass
    return cfg
