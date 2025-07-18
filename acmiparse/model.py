from typing import Optional, List, Dict, Union
from dataclasses import dataclass, field

class ACMIPropertyRegistry:
    GLOBAL_PROPERTIES_ALLOWED_TEXT_KEYS: List[str] = ["DataSource", "DataRecorder", "ReferenceTime", "RecordingTime", "Author", "Title", "Category", "Briefing", "Debriefing", "Comments", "MapId"]
    GLOBAL_PROPERTIES_ALLOWED_NUMERIC_KEYS: List[str] = ["ReferenceLongitude", "ReferenceLatitude"]
    # 内置的字符串列表（类级常量，不会参与 __init__）
    OBJECT_PROPERTIES_ALLOWED_TEXT_KEYS: List[str] = ["Name", "Type", "AdditionalType", "Parent", "Next", "ShortName", "LongName", "FullName", "CallSign", "Registration", "Squawk", "ICAO24",
                "Pilot", "Group", "Country", "Coalition", "Color", "Shape", "Debug", "Label", "FocusedTarget", "LockedTarget"] + [f"LockedTarget{i}" for i in range(1, 10)]
    OBJECT_PROPERTIES_ALLOWED_NUMERIC_KEYS: List[str] = ["Importance", "Slot", "Disabled", "Visible", "Health", "Length", "Width", "Height", "Radius", "IAS", "CAS", "TAS", "Mach", "AltimeterSetting", 
                "OnGround", "AOA", "AOS", "AGL", "HDG", "HDM", "Throttle", "Throttle2", "EngineRPM", "EngineRPM2", "NR", "NR2", "RotorRPM", "RotorRPM2", 
                "Afterburner", "AirBrakes", "Flaps", "LandingGear", "LandingGearHandle", "Tailhook", "Parachute", "DragChute", "FuelWeight", "FuelVolume", 
                "FuelFlowWeight", "FuelFlowVolume"] + [f"FuelWeight{i}" for i in range(1, 10)] + [f"FuelVolume{i}" for i in range(1, 10)] + [f"FuelFlowWeight{i}" for i in range(1, 9)] + [
                f"FuelFlowVolume{i}" for i in range(1, 9)] + ["RadarMode", "RadarAzimuth", "RadarElevation", "RadarRoll", "RadarRange", "RadarHorizontalBeamwidth", 
                "RadarVerticalBeamwidth", "RadarRangeGateAzimuth", "RadarRangeGateElevation", "RadarRangeGateRoll", "RadarRangeGateMin", "RadarRangeGateMax", 
                "RadarRangeGateHorizontalBeamwidth", "RadarRangeGateVerticalBeamwidth", "LockedTargetMode", "LockedTargetAzimuth", "LockedTargetElevation", "LockedTargetRange", 
                "EngagementMode", "EngagementMode2", "EngagementRange", "EngagementRange2", "VerticalEngagementRange", "VerticalEngagementRange2", "RollControlInput", "PitchControlInput", "YawControlInput",
                "RollControlPosition", "PitchControlPosition", "YawControlPosition", "RollTrimTab", "PitchTrimTab", "YawTrimTab", "AileronLeft", "AileronRight", "Elevator", "Rudder", 
                "LocalizerLateralDeviation", "GlideslopeVerticalDeviation", "LocalizerAngularDeviation", "GlideslopeAngularDeviation", "PilotHeadRoll", "PilotHeadPitch", "PilotHeadYaw",
                "PilotEyeGazePitch", "PilotEyeGazeYaw", "VerticalGForce", "LongitudinalGForce", "LateralGForce", "QNH", "WindDirection", "WindPitch", "WindSpeed", "TriggerPressed",
                "ENL", "HeartRate", "SpO2"]


@dataclass
class ACMIHeader:
    file_type: str = "text/acmi/tacview"
    file_version: str = "2.2"
    # reference_time: Optional[str] = None  # UTC 时间字符串
    # recording_time: Optional[str] = None  # UTC 时间字符串
    # data_source: Optional[str] = None
    # data_recorder: Optional[str] = None
    # author: Optional[str] = None
    # title: Optional[str] = None
    # category: Optional[str] = None
    # briefing: Optional[str] = None
    # debriefing: Optional[str] = None
    # comments: Optional[str] = None
    # map_id: Optional[str] = None
    # reference_latitude: Optional[float] = None # deg
    # reference_longitude: Optional[float] = None # deg
    # other_properties: Dict[str, str] = None  # 其他非标准属性

    # def __post_init__(self):
    #     if self.other_properties is None:
    #         self.other_properties = {}

@dataclass
class ACMIObjectCoordinates:
    object_id: int
    type: str = 'simple+spherical' # simple complex spherical flat 
    longitude: Optional[float] = None # 经度
    latitude: Optional[float] = None # 纬度
    altitude: Optional[float] = None # 高度 / 米
    pitch: Optional[float] = None  # 度
    yaw: Optional[float] = None    # 度
    roll: Optional[float] = None   # 度
    u: Optional[float] = None  # m/s
    v: Optional[float] = None  # m/s
    heading: Optional[float] = None  # 

@dataclass
class ACMIGlobalProperties: # 全局属性, 文件开始处除了前两行的属性
    text_properties: Dict[str, str] = None  # 文本属性
    numeric_properties: Dict[str, float] = None # 数值属性

    # # 内置的字符串列表（类级常量，不会参与 __init__）
    # ALLOWED_TEXT_KEYS: List[str] = field(
    #     default_factory=lambda: ["DataSource", "DataRecorder", "ReferenceTime", "RecordingTime", "Author", "Title", "Category", "Briefing", "Debriefing", "Comments", "MapId"],
    #     init=False,            # 不让它出现在构造函数签名中
    #     repr=False             # 不让它出现在 repr 输出
    # )
    # ALLOWED_NUMERIC_KEYS: List[str] = field(
    #     default_factory=lambda: ["ReferenceLongitude", "ReferenceLatitude"],
    #     init=False,            # 不让它出现在构造函数签名中
    #     repr=False             # 不让它出现在 repr 输出
    # )
    
@dataclass
class ACMIEvent:
    object_id: int
    event_type: str # 事件类型
    object_ids: List[int] # 对象id列表
    event_text: str # 事件文本

@dataclass
class ACMIObjectProperties:
    text_properties: Dict[str, str] = None
    numeric_properties: Dict[str, float] = None

    # # 内置的字符串列表（类级常量，不会参与 __init__）
    # ALLOWED_TEXT_KEYS: List[str] = field(
    #     default_factory=lambda: ["Name", "Type", "AdditionalType", "Parent", "Next", "ShortName", "LongName", "FullName", "CallSign", "Registration", "Squawk", "ICAO24"
    #                              , "Pilot", "Group", "Country", "Coalition", "Color", "Shape", "Debug", "Label", "FocusedTarget", "LockedTarget"] + [f"LockedTarget{i}" for i in range(1, 10)],
    #     init=False,            # 不让它出现在构造函数签名中
    #     repr=False             # 不让它出现在 repr 输出
    # )
    # ALLOWED_NUMERIC_KEYS: List[str] = field(
    #     default_factory=lambda: ["Importance", "Slot", "Disabled", "Visible", "Health", "Length", "Width", "Height", "Radius", "IAS", "CAS", "TAS", "Mach", "AltimeterSetting", 
    #                              "OnGround", "AOA", "AOS", "AGL", "HDG", "HDM", "Throttle", "Throttle2", "EngineRPM", "EngineRPM2", "NR", "NR2", "RotorRPM", "RotorRPM2", 
    #                              "Afterburner", "AirBrakes", "Flaps", "LandingGear", "LandingGearHandle", "Tailhook", "Parachute", "DragChute", "FuelWeight", "FuelVolume", 
    #                              "FuelFlowWeight", "FuelFlowVolume"] + [f"FuelWeight{i}" for i in range(1, 10)] + [f"FuelVolume{i}" for i in range(1, 10)] + [f"FuelFlowWeight{i}" for i in range(1, 9)] + 
    #                              [f"FuelFlowVolume{i}" for i in range(1, 9)] + ["RadarMode", "RadarAzimuth", "RadarElevation", "RadarRoll", "RadarRange", "RadarHorizontalBeamwidth", 
    #                              "RadarVerticalBeamwidth", "RadarRangeGateAzimuth", "RadarRangeGateElevation", "RadarRangeGateRoll", "RadarRangeGateMin", "RadarRangeGateMax", 
    #                              "RadarRangeGateHorizontalBeamwidth", "RadarRangeGateVerticalBeamwidth", "LockedTargetMode", "LockedTargetAzimuth", "LockedTargetElevation", "LockedTargetRange", 
    #                              "EngagementMode", "EngagementMode2", "EngagementRange", "EngagementRange2", "VerticalEngagementRange", "VerticalEngagementRange2", "RollControlInput", "PitchControlInput", "YawControlInput",
    #                              "RollControlPosition", "PitchControlPosition", "YawControlPosition", "RollTrimTab", "PitchTrimTab", "YawTrimTab", "AileronLeft", "AileronRight", "Elevator", "Rudder", 
    #                              "LocalizerLateralDeviation", "GlideslopeVerticalDeviation", "LocalizerAngularDeviation", "GlideslopeAngularDeviation", "PilotHeadRoll", "PilotHeadPitch", "PilotHeadYaw",
    #                              "PilotEyeGazePitch", "PilotEyeGazeYaw", "VerticalGForce", "LongitudinalGForce", "LateralGForce", "QNH", "WindDirection", "WindPitch", "WindSpeed", "TriggerPressed",
    #                              "ENL", "HeartRate", "SpO2"],
    #     init=False,            # 不让它出现在构造函数签名中
    #     repr=False             # 不让它出现在 repr 输出
    # )


@dataclass
class ACMIObject: # 一行内容
    object_id: int
    time_offset: float  # 相对于 ReferenceTime 的秒数
    
    object_coordinates: ACMIObjectCoordinates = None
    object_properties: ACMIGlobalProperties = None
    object_events: ACMIEvent = None


@dataclass
class ACMIFrame:
    timestamp: float  # 相对于 ReferenceTime 的秒数
    objects: List[ACMIObject]

@dataclass
class ACMIFile:
    header: ACMIHeader
    global_properties: ACMIGlobalProperties
    frames: List[ACMIFrame]
