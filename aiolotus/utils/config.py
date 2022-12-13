from typing import Optional, Dict
from lazyops.types import BaseSettings, lazyproperty
from aiolotus.version import VERSION

class LotusWorkerSettings(BaseSettings):
    enabled: Optional[bool] = True

    max_msg_size: Optional[int] = 32 << 10
    # Our servers only accept batches less than 500KB. Here limit is set slightly
    # lower to leave space for extra data that will be added later, eg. "sentAt".
    batch_size_limit: Optional[int] = 475000

    flush_at: Optional[int] = 100
    flush_interval: Optional[float] = 0.5
    max_queue_size: Optional[int] = 1000

    class Config:
        env_prefix = "LOTUS_WORKER_"
        case_sensitive = False


class LotusSettings(BaseSettings):

    url: Optional[str] = None
    scheme: Optional[str] = 'http://'
    host: Optional[str] = None
    port: Optional[int] = 8000
    
    apikey: Optional[str] = None
    apipath: Optional[str] = None

    apikey_header: Optional[str] = 'X-API-KEY'

    gzip_enabled: Optional[bool] = False
    num_workers: Optional[int] = 4
    # Fallsback to num_workers if not set
    num_pool_workers: Optional[int] = None

    ignore_errors: Optional[bool] = True
    debug_enabled: Optional[bool] = False

    timeout: Optional[int] = 10
    max_retries: Optional[int] = 3
    
    send_enabled: bool = True
    sync_enabled: bool = False
    timeout: int = 10
    threads: int = 1
    
    class Config:
        env_prefix = 'LOTUS_'
        case_sensitive = False

    @lazyproperty
    def worker(self) -> LotusWorkerSettings:
        return LotusWorkerSettings()
    
    @lazyproperty
    def api_url(self) -> str:
        if self.url:
            return self.url
        if self.host:
            url = f"{self.scheme}{self.host}"
            if self.port: url += f":{self.port}"
            return url
        
        # Return the official Lotus API URL
        return "https://www.uselotus.app"
        # raise ValueError("Lotus API URL is not specified")
    
    @lazyproperty
    def headers(self):
        _headers = {"Content-Type": "application/json", "User-Agent": f"aiolotus/{VERSION}"}
        if self.apikey: _headers[self.apikey_header] = self.apikey
        return _headers


    def get_headers(self, apikey: Optional[str] = None, apikey_header: Optional[str] = None, **kwargs) -> Dict[str, str]:
        headers = self.headers.copy()
        if kwargs: headers.update(**kwargs)
        apikey_header = apikey_header or self.apikey_header
        apikey = apikey or self.apikey
        if apikey: headers[apikey_header] = apikey
        return headers

    def get_api_url(self, host: Optional[str] = None, port: Optional[int] = None, scheme: Optional[str] = None, url: Optional[str] = None) -> str:
        if url: return url
        if host:
            url = f"{scheme or self.scheme}{host}"
            if port: url += f":{port}"
            return url
        return self.api_url


settings = LotusSettings()