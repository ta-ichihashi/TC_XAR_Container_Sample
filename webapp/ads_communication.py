import pyads
import ctypes
from dataclasses import dataclass, field
from typing import List, Tuple, Callable, Generic, TypeVar
from zoneinfo import ZoneInfo
import platform
import asyncio
from collections import OrderedDict

T = TypeVar('T')

@dataclass
class EventNotificator(Generic[T]):
    connection: pyads.Connection
    model: T
    subscriber: Callable
    symbol: str
    cycle_time : int = field(default=1)

    def __post_init__(self):
        try:
            if isinstance(self.model, tuple):
                size_of_struct = pyads.size_of_structure(self.model)
                attr = pyads.NotificationAttrib(size_of_struct)
                attr.trans_mode = pyads.ADSTRANS_SERVERONCHA
                attr.max_delay = 100
                attr.cycle_time = self.cycle_time
                @self.connection.notification(ctypes.c_ubyte * size_of_struct)
                def callback(handle, name, timestamp, value):
                    timestamp = timestamp.replace(tzinfo=ZoneInfo("UTC"))
                    self.subscriber(timestamp, value)
                self.connection.add_device_notification(self.symbol,
                                            attr,
                                            callback)
            else:
                attr = pyads.NotificationAttrib(ctypes.sizeof(self.model))
                attr.trans_mode = pyads.ADSTRANS_SERVERONCHA
                attr.max_delay = 100
                attr.cycle_time = self.cycle_time
                tags = {self.symbol : pyads.PLCTYPE_ULINT}

                def callback(notification, data):
                    data_type = tags[data]
                    handle, timestamp, value = self.connection.parse_notification(notification, data_type, True)
                    timestamp = timestamp.replace(tzinfo=ZoneInfo("UTC"))
                    self.subscriber(timestamp, value)

                self.connection.add_device_notification(self.symbol,
                                            attr,
                                            callback)
        except pyads.pyads_ex.ADSError:
            print(f"Symbol not found: {self.symbol}")

@dataclass
class RouterConfiguration:
    target_host: str = field(default='192.168.20.3')
    target_host_name: str = field(default = 'tc-xar-1')
    my_ams_id: str = field(default='127.0.0.1.1.1')
    route_name: str = field(default='127.0.0.1')
    login_user: str = field(default='Administrator')
    login_password: str = field(default='1')

    def connect(self):
        pyads.open_port()
        pyads.set_local_address(RouterConfiguration.my_ams_id)
        pyads.add_route_to_plc(RouterConfiguration.my_ams_id,
                            RouterConfiguration.target_host_name,
                            RouterConfiguration.target_host,
                            RouterConfiguration.login_user,
                            RouterConfiguration.login_password,
                            route_name=RouterConfiguration.route_name)
    def disconnect(self):
            pyads.close_port()

@dataclass
class AdsCommunication:
    ams_net_id: str = field(default='127.0.0.1.1.1')
    ads_port: int = field(default=851, init=True)
    ads_router: RouterConfiguration = field(default=None)
    event_notificators: List[EventNotificator] = field(default_factory=list, init=False)
    connection: pyads.Connection = field(default=None, init=False)
    symbols :List[pyads.symbol.AdsSymbol] = field(default_factory=list, init=False)

    def __post_init__(self):
        if self.ads_router is not None:
            self.ads_router.connect()
        self.connection = pyads.Connection(self.ams_net_id, self.ads_port)
        self.connection.open()
        #self.symbols = self.connection.get_all_symbols()
        for symbol in self.symbols:
            print(symbol.name)

    def reg_notification(self,symbol: str, model: tuple, subscriber: Callable, cycle_time: int = 1):
        self.event_notificators.append(
            EventNotificator[tuple](
                connection=self.connection,
                model=model,
                subscriber=subscriber,
                symbol=symbol,
                cycle_time=cycle_time
            )
        )

    def write(self,symbol: str, value, type):
        self.connection.write_by_name(symbol, value, type)


@dataclass
class EventReporter:
    plc : AdsCommunication = field(default=None, init=True)
    mapping_structure : Tuple[Tuple] = field(default_factory=Tuple, init=True)
    mapping_symbol : str = field(default_factory=str, init=True)
    cycle_time  : int = field(default=10)
    queue: asyncio.Queue = field(default=None)
    queue_size : int = field(default=0)
    packkaged_num : int = field(default=1)

    def __post_init__(self):
        self.queue = asyncio.Queue(maxsize=self.queue_size)
        self.packkage = dict()
        # 監視したい変数とデータ構造を定義したtupleを登録
        self.plc.reg_notification(
            self.mapping_symbol,
            self.mapping_structure,
            self.job_event_handler,
            self.cycle_time
        )

    def _put_data(self, timestamp, value):
        data = pyads.dict_from_bytes(value, self.mapping_structure)
        self.packkage = self.packkage | {key : [] for key in data.keys() if key not in self.packkage}
        if "timestamp" not in self.packkage:
            self.packkage["timestamp"] = []
        for key in data.keys():
            self.packkage[key].append(data.get(key))
        self.packkage["timestamp"].append(timestamp)
        if len(self.packkage["timestamp"]) >= self.packkaged_num:
            self.queue.put_nowait(self.packkage)
            self.packkage = dict()

    def job_event_handler(self, timestamp, value):
        self._put_data(timestamp, value)
