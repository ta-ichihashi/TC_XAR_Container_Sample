import tomllib
import streamlit as st
import streamlit.components.v1 as stc
from model import job_event_structure, axis_to_plc_structure
from ads_communication import AdsCommunication, EventReporter, RouterConfiguration
from dataclasses import dataclass, field
from typing import Any
import const
import platform
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfo
import os

class TwinCATTime:
    EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
    DC_BASETIME = datetime(year=2000,month=1,day=1,hour=0,minute=0,second=0)
    EPOCH_AS_DCTIME = 0 - (int(time.mktime(DC_BASETIME.timetuple()) * 1000) + int(DC_BASETIME.microsecond / 1000))  * 10000000 # January 1, 1970 as DC time(ns)
    HUNDREDS_OF_NANOSECONDS = 10000000
    NANOSECONDS = 1000000000


    @classmethod
    def get_dc_time_h32(cls) -> int:
        now = datetime.now()
        ns_now = (int(time.mktime(now.timetuple()) * 1000) + int(now.microsecond / 1000))  * 10000000
        dctime_now = ns_now - cls.EPOCH_AS_DCTIME
        h_32bit = dctime_now & 0xffffffff00000000
        return h_32bit



    @classmethod
    def filetime_to_dt(cls, ft):
        """Converts a Microsoft filetime number to a Python datetime. The new datetime object is time zone-naive but is equivalent to tzinfo=utc.

        >>> filetime_to_dt(116444736000000000)
        datetime.datetime(1970, 1, 1, 0, 0)
        """
        # Get seconds and remainder in terms of Unix epoch
        (s, ns100) = divmod(ft - cls.EPOCH_AS_FILETIME, cls.HUNDREDS_OF_NANOSECONDS)
        # Convert to datetime object
        dt = datetime.fromtimestamp(s)
        # Add remainder in as microseconds. Python 3.2 requires an integer
        dt = dt.replace(microsecond=(ns100 // 10))
        return dt

    @classmethod
    def dctime_to_dt(cls, ft):
        # Get seconds and remainder in terms of Unix epoch
        (s, ns) = divmod(ft - cls.EPOCH_AS_DCTIME, cls.NANOSECONDS)
        # Convert to datetime object
        dt = datetime.fromtimestamp(s)
        # Add remainder in as microseconds. Python 3.2 requires an integer
        dt = dt.replace(microsecond=(ns // 1000))
        return dt

@dataclass
class JobWatcher:
    ams_net_id : str = field(default="127.0.0.1.1.1")
    ads_port : int = field(default=851)
    view_data   : pd.DataFrame = field(default=None)
    row_size : int = field(default=80)

    def __post_init__(self):
        self.view_data = pd.DataFrame(index=["job_id"], columns=["Task", "Start", "Finish", "State"])
        plc_connector = AdsCommunication(ams_net_id=self.ams_net_id, ads_port=self.ads_port)
        self.event_manager = EventReporter(plc=plc_connector,
                                         mapping_structure=job_event_structure,
                                         mapping_symbol='demo3.runner.fbObserver.event_message',
                                         packkaged_num=1)

    def get_record(self):
        while not self.event_manager.queue.empty():
            get_collection = self.event_manager.queue.get_nowait()
            for i, value in enumerate(get_collection["timestamp"]):
                record = {key : get_collection[key][i] for key in get_collection}
                timestamp = record["timestamp"]
                timestamp = timestamp.astimezone(ZoneInfo("Japan"))
                if record["new_state"] == 'process' and record["old_state"] == 'wait_for_process':
                    self.view_data.loc[record["job_id"]] = [record["subject"], timestamp, pd.NA, "Process"]

                elif record["old_state"] == 'process':
                    self.view_data.loc[record["job_id"],["Finish"]] = timestamp
                    self.view_data.loc[record["job_id"],["State"]] = record["new_state"]
            #self.view_data = self.view_data.dropna(subset=["Start", "Finish"])
            self.view_data = self.view_data.tail(self.row_size)

@dataclass
class MotionWatcher:
    ams_net_id : str
    ads_port : int = field(default=851)
    view_data   : pd.DataFrame = field(default_factory=pd.DataFrame)
    row_size : int = field(default=100)
    thining  : int = field(default=100)

    def __post_init__(self):
        plc_connector = AdsCommunication(ams_net_id=self.ams_net_id, ads_port=501)
        self.event_manager = EventReporter(plc=plc_connector,
                                         mapping_structure=axis_to_plc_structure,
                                         mapping_symbol='Axes.Axis 1.ToPlc',
                                         packkaged_num=1000)

    def get_record(self):
        while not self.event_manager.queue.empty():
            get_collection = self.event_manager.queue.get_nowait()
            _df = pd.DataFrame.from_dict(get_collection)
            _df = _df[::self.thining]
            self.view_data = pd.concat([self.view_data, _df])
        self.view_data = self.view_data.tail(self.row_size)

@dataclass
class DynamicRender:
    ams_net_id : str

    def __post_init__(self):
        self.job_observer = JobWatcher(ams_net_id=self.ams_net_id)
        self.motion_observer = MotionWatcher(ams_net_id=self.ams_net_id)
        self.chart_spec = dict()

    def render_job_gantt(self, placeholder):
        self.job_observer.get_record()
        self.chart_spec = {
            "data": {"values": self.job_observer.view_data.dropna().to_dict("records")}, # Pandas DataFrameをレコードのリストに変換
            "mark": "bar",
            "encoding": {
                "y": {"field": "Task", "sort": None}, # タスク名をY軸に表示
                "x": {"field": "Start", "type": "temporal", "title": "開始"}, # 開始日をX軸に
                "x2": {"field": "Finish", "type": "temporal", "title": "終了"}, # 終了日を範囲の終点に
                "color": {"field": "Task", "legend": None} # タスクごとに色分け
            },
            "width": 600,
            "height": 200
        }
        placeholder.vega_lite_chart(self.chart_spec, width='stretch')

    def render_motion_activity(self, table, timeline_pos, timeline_posdiff):
        self.motion_observer.get_record()
        if len(self.motion_observer.view_data) > 0:
            with table:
                if "timestamp" in self.motion_observer.view_data.columns:
                    df = self.motion_observer.view_data.set_index("timestamp")
                st.dataframe(df)
            with timeline_pos:
                df = self.motion_observer.view_data
                st.line_chart(df, x="timestamp", y=["SetPos", "ActPos","SetVelo", "ActVelo"], x_label="時刻", y_label="位置(mm) / 速度 (mm/s)")
            with timeline_posdiff:
                df = self.motion_observer.view_data
                st.line_chart(df, x="timestamp", y=["PosDiff"], x_label="時刻", y_label="位置偏差(mm)")

class View:
    router : RouterConfiguration
    settings_data : dict[str, Any]

    @classmethod
    def connect_target(cls):
        pass

    @classmethod
    def get_settings(cls):
        # 設定データ
        toml_file_path: str = "settings.toml"
        with open(toml_file_path, mode="rb") as toml_file:
            cls.settings_data = tomllib.load(toml_file)
        if os.environ.get("CONTAINER1_HOSTNAME") is not None:
            cls.settings_data["container"][0]["hostname"] = os.environ["CONTAINER1_HOSTNAME"]
        if os.environ.get("CONTAINER2_HOSTNAME") is not None:
            cls.settings_data["container"][1]["hostname"] = os.environ["CONTAINER2_HOSTNAME"]
        if os.environ.get("CONTAINER1_ADDRESS") is not None:
            cls.settings_data["container"][0]["host"] = os.environ["CONTAINER1_ADDRESS"]
        if os.environ.get("CONTAINER2_ADDRESS") is not None:
            cls.settings_data["container"][1]["host"] = os.environ["CONTAINER2_ADDRESS"]
        if os.environ.get("CONTAINER1_AMSID") is not None:
            cls.settings_data["container"][0]["ams_net_id"] = os.environ["CONTAINER1_AMSID"]
        if os.environ.get("CONTAINER2_AMSID") is not None:
            cls.settings_data["container"][1]["ams_net_id"] = os.environ["CONTAINER2_AMSID"]
        if os.environ.get("CONTAINER1_PLCHMI_URL") is not None:
            cls.settings_data["container"][0]["plc_hmi_url"] = os.environ["CONTAINER1_PLCHMI_URL"]
        if os.environ.get("CONTAINER2_PLCHMI_URL") is not None:
            cls.settings_data["container"][1]["plc_hmi_url"] = os.environ["CONTAINER2_PLCHMI_URL"]
        if os.environ.get("MY_AMSID") is not None:
            cls.settings_data["my_ams_net_id"] = os.environ["MY_AMSID"]
        if os.environ.get("MY_ADDRESS") is not None:
            cls.settings_data["my_host"] = os.environ["MY_ADDRESS"]

    @classmethod
    def render_sidebar(cls):
        with st.sidebar:
            st.logo("assets/beckhoff.icon.jpeg", icon_image="assets/beckhoff.icon.jpeg")
            st.header("BECKHOFF")

    @classmethod
    def get_iframe(cls, url:str, height : int, width:str = "100%") -> stc.declare_component:
        html_code = f"""
            <iframe src="{url}" width="{width}" height="{height}"></iframe>
            """

        return stc.html(html_code, height=height)



    @classmethod
    def render(cls):
    #def render(cls,container1_dynamic_render, container2_dynamic_render ):
        cls.render_sidebar()
        st.set_page_config(
            page_title="Virtual Controller DEMO powerd by TwinCAT RT Linux",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'About': "https://beckhoff-jp.github.io/TwinCATHowTo/twincat_container/index.html#id2"
            }
            )

        # Remove header blank
        st.markdown("""
        <style>
                /* Remove blank space at top and bottom */
                .block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                }

        </style>
        """, unsafe_allow_html=True)

        cols_header = st.columns([2,6,2], gap=None, border=False, vertical_alignment = "center", width="stretch")
        with cols_header[0]:
            st.image("assets/teaser_Beckhoff_TwinCAT_runtime_for_real-time_Linux.jpg", width="stretch")
        with cols_header[1]:
            st.markdown(
                """
                <h2 style="text-align: center; margin-top: 0;">
                    TwinCAT RT Linuxによる<BR>バーチャルPLCデモ
                </h2>
                """,
                unsafe_allow_html=True
            )
            # st.title("TwinCAT RT Linux DEMO", width="content")
            st.markdown(const.HIDE_ST_STYLE, unsafe_allow_html=True)
        with cols_header[2]:
            st.image("assets/Beckhoff_logo_red_cmyk.svg", width="stretch")

        #with st.popbar(horizontal=True, gap="medium"):
        #cols = st.columns(2, gap="medium", width="stretch", vertical_alignment = "center")
        cols = st.tabs(["TwinCAT コンテナ1","TwinCAT コンテナ2"])
        #with cols[0]:
        #    st.header("TwinCAT コンテナ1", divider = "red")
            #st.write("TF1810 PLC HMI Web")
        #with cols[1]:
        #    st.header("TwinCAT コンテナ2", divider = "red")
            #st.write("TF1810 PLC HMI Web")
        with cols[0].container(border=True, height="stretch"):
            url = st.text_input("TF1810 PLC HMI Web",value=View.settings_data["container"][0]["plc_hmi_url"],label_visibility="collapsed")
            View.get_iframe(url,height = 300)
        with cols[1].container(border=True, height="stretch"):
            url = st.text_input("TF1810 PLC HMI Web",value=View.settings_data["container"][1]["plc_hmi_url"],label_visibility="collapsed")
            View.get_iframe(url,height = 300)
        with cols[0].container(border=True, height="stretch"):
            c1_jobgannt = st.empty()
        with cols[1].container(border=True, height="stretch"):
            c2_jobgannt = st.empty()
        with cols[0].container(border=True, height="stretch"):
            c1_motion_table = st.empty()
        with cols[1].container(border=True, height="stretch"):
            c2_motion_table = st.empty()
        with cols[0].container(border=True, height="stretch"):
            c1_timeline_pos = st.empty()
        with cols[1].container(border=True, height="stretch"):
            c2_timeline_pos = st.empty()
        with cols[0].container(border=True, height="stretch"):
            c1_timeline_posdiff = st.empty()
        with cols[1].container(border=True, height="stretch"):
            c2_timeline_posdiff = st.empty()
        container1_dynamic_render = DynamicRender(cls.settings_data["container"][0]["ams_net_id"])
        container2_dynamic_render = DynamicRender(cls.settings_data["container"][1]["ams_net_id"])
        while True:
            container1_dynamic_render.render_job_gantt(c1_jobgannt)
            container2_dynamic_render.render_job_gantt(c2_jobgannt)
            container1_dynamic_render.render_motion_activity(c1_motion_table, c1_timeline_pos, c1_timeline_posdiff)
            container2_dynamic_render.render_motion_activity(c2_motion_table, c2_timeline_pos, c2_timeline_posdiff)
            time.sleep(1)


if __name__ == '__main__':
    View.get_settings()
    if platform.system() == 'Linux':
        RouterConfiguration(target_host=View.settings_data["container"][0]["host"],
                            my_host=View.settings_data["my_host"],
                            my_ams_id=View.settings_data["my_ams_net_id"],
                            route_name="tc31-xar-1",
                            login_user="Administrator",
                            login_password="1"
                            )
        RouterConfiguration.add_route()
        RouterConfiguration(target_host=View.settings_data["container"][1]["host"],
                            my_host=View.settings_data["my_host"],
                            my_ams_id=View.settings_data["my_ams_net_id"],
                            route_name="tc31-xar-2",
                            login_user="Administrator",
                            login_password="1"
                            )
        RouterConfiguration.add_route()
    View.render()
