# -*- coding: utf-8 -*-
"""
🎤 豆包TTS音色数据库

将音色数据结构化存储，支持两种输出格式：
1. JSON 数组格式 - 用于程序调用
2. Markdown 格式 - 用于 LLM 提示词

使用示例：
    from .voice_database import VoiceDatabase
    
    db = VoiceDatabase()
    
    # 获取 JSON 格式
    voices = db.get_voices_json()
    
    # 获取 Markdown 格式提示词
    prompt = db.get_voices_markdown()
    
    # 按分类筛选
    female_voices = db.get_voices_by_gender("female")
    v2_voices = db.get_voices_by_version("2.0")
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class VoiceGender(str, Enum):
    """音色性别"""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceVersion(str, Enum):
    """音色版本"""
    V2 = "2.0"
    V1_EMO = "1.0_emo"
    ROLEPLAY = "roleplay"
    DIALECT = "dialect"
    IP = "ip"
    VIDEO = "video"
    CS = "customer_service"
    ENGLISH = "english"
    MULTI = "multilingual"


@dataclass
class VoiceInfo:
    """音色信息"""
    name: str                    # 展示名称
    voice_type: str             # voice_type ID
    gender: VoiceGender         # 性别
    language: str               # 语种
    description: str            # 特点描述
    scenarios: str              # 适用场景
    version: VoiceVersion       # 版本分类
    category: str               # 细分类别
    emotions: Optional[List[str]] = None  # 支持的情感（仅情感音色）
    capabilities: Optional[List[str]] = None  # 支持能力


# ============================================================================
# 音色数据定义
# ============================================================================

VOICE_DATA: List[VoiceInfo] = [
    # ========== 一、通用高质量音色（2.0版本） ==========
    # 女声
    VoiceInfo("Vivi 2.0", "zh_female_vv_uranus_bigtts", VoiceGender.FEMALE, "中文、英语",
              "年轻女性，声音清晰自然，情感表达丰富", "通用场景、旁白、讲解、对话",
              VoiceVersion.V2, "通用高质量", capabilities=["情感变化", "指令遵循", "ASMR"]),
    VoiceInfo("小何 2.0", "zh_female_xiaohe_uranus_bigtts", VoiceGender.FEMALE, "中文",
              "年轻女性，声音温柔亲切，自然流畅", "通用场景、旁白、客服、助手",
              VoiceVersion.V2, "通用高质量", capabilities=["情感变化", "指令遵循", "ASMR"]),
    VoiceInfo("儿童绘本", "zh_female_xueayi_saturn_bigtts", VoiceGender.FEMALE, "中文",
              "温柔活泼，适合儿童内容", "儿童故事、绘本朗读、教育内容",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循"]),
    VoiceInfo("黑猫侦探社咪", "zh_female_mizai_saturn_bigtts", VoiceGender.FEMALE, "中文",
              "活泼俏皮，有趣味性", "动画配音、趣味视频、儿童内容",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循"]),
    VoiceInfo("鸡汤女", "zh_female_jitangnv_saturn_bigtts", VoiceGender.FEMALE, "中文",
              "温暖治愈，富有感染力", "励志内容、情感电台、心灵鸡汤",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循"]),
    VoiceInfo("魅力女友", "zh_female_meilinvyou_saturn_bigtts", VoiceGender.FEMALE, "中文",
              "甜美温柔，有亲和力", "情感内容、陪伴对话、恋爱场景",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循"]),
    VoiceInfo("流畅女声", "zh_female_santongyongns_saturn_bigtts", VoiceGender.FEMALE, "中文",
              "标准清晰，专业流畅", "视频配音、产品介绍、通用内容",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循"]),
    VoiceInfo("可爱女生", "saturn_zh_female_keainvsheng_tob", VoiceGender.FEMALE, "中文",
              "可爱甜美，活泼开朗，少女感", "角色扮演、萌系角色、年轻女性角色",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循", "COT/QA功能"]),
    VoiceInfo("调皮公主", "saturn_zh_female_tiaopigongzhu_tob", VoiceGender.FEMALE, "中文",
              "调皮任性，娇俏可爱，小公主气质", "角色扮演、公主角色、娇蛮角色",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循", "COT/QA功能"]),
    VoiceInfo("知性灿灿", "saturn_zh_female_cancan_tob", VoiceGender.FEMALE, "中文",
              "知性优雅，成熟稳重", "角色扮演、职场女性、知性角色",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循", "COT/QA功能"]),
    # 男声
    VoiceInfo("云舟 2.0", "zh_male_m191_uranus_bigtts", VoiceGender.MALE, "中文",
              "成熟男性，声音磁性低沉，稳重可靠", "通用场景、旁白、讲解、正式场合",
              VoiceVersion.V2, "通用高质量", capabilities=["情感变化", "指令遵循", "ASMR"]),
    VoiceInfo("小天 2.0", "zh_male_taocheng_uranus_bigtts", VoiceGender.MALE, "中文",
              "年轻男性，声音阳光清朗，有活力", "通用场景、年轻角色、活泼场景",
              VoiceVersion.V2, "通用高质量", capabilities=["情感变化", "指令遵循", "ASMR"]),
    VoiceInfo("大壹", "zh_male_dayi_saturn_bigtts", VoiceGender.MALE, "中文",
              "大气稳重，专业可靠", "视频配音、纪录片、正式内容",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循"]),
    VoiceInfo("儒雅逸辰", "zh_male_ruyayichen_saturn_bigtts", VoiceGender.MALE, "中文",
              "儒雅温润，书卷气息", "视频配音、文化内容、古风内容",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循"]),
    VoiceInfo("爽朗少年", "saturn_zh_male_shuanglangshaonian_tob", VoiceGender.MALE, "中文",
              "阳光爽朗，青春活力，少年感", "角色扮演、少年角色、热血角色",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循", "COT/QA功能"]),
    VoiceInfo("天才同桌", "saturn_zh_male_tiancaitongzhuo_tob", VoiceGender.MALE, "中文",
              "聪明伶俐，少年感，略带傲气", "角色扮演、学生角色、天才角色",
              VoiceVersion.V2, "通用高质量", capabilities=["指令遵循", "COT/QA功能"]),
              
    # ========== 二、多情感音色（1.0版本） ==========
    # 女声
    VoiceInfo("甜心小美", "zh_female_tianxinxiaomei_emo_v2_mars_bigtts", VoiceGender.FEMALE, "中文",
              "甜美可爱，少女感强", "甜美女性角色、可爱角色",
              VoiceVersion.V1_EMO, "多情感", emotions=["悲伤", "恐惧", "厌恶", "中性"]),
    VoiceInfo("高冷御姐", "zh_female_gaolengyujie_emo_v2_mars_bigtts", VoiceGender.FEMALE, "中文",
              "冷艳高傲，御姐气质，成熟性感", "御姐角色、冷艳女性、女王角色",
              VoiceVersion.V1_EMO, "多情感", emotions=["开心", "悲伤", "生气", "惊讶", "恐惧", "厌恶", "激动", "冷漠", "中性"]),
    VoiceInfo("邻居阿姨", "zh_female_linjuayi_emo_v2_mars_bigtts", VoiceGender.FEMALE, "中文",
              "亲切热情，中年女性，邻里感", "中年女性角色、母亲角色、阿姨角色",
              VoiceVersion.V1_EMO, "多情感", emotions=["中性", "愤怒", "冷漠", "沮丧", "惊讶"]),
    VoiceInfo("柔美女友", "zh_female_roumeinvyou_emo_v2_mars_bigtts", VoiceGender.FEMALE, "中文",
              "温柔体贴，柔情似水", "温柔女性、女友角色、贤淑女性",
              VoiceVersion.V1_EMO, "多情感", emotions=["开心", "悲伤", "生气", "惊讶", "恐惧", "厌恶", "激动", "冷漠", "中性"]),
    VoiceInfo("魅力女友", "zh_female_meilinvyou_emo_v2_mars_bigtts", VoiceGender.FEMALE, "中文",
              "甜美有魅力，温柔可人", "女友角色、甜美女性",
              VoiceVersion.V1_EMO, "多情感", emotions=["悲伤", "恐惧", "中性"]),
    VoiceInfo("爽快思思", "zh_female_shuangkuaisisi_emo_v2_mars_bigtts", VoiceGender.FEMALE, "中文、英式英语",
              "爽朗直率，开朗大方", "开朗女性、朋友角色、活泼女性",
              VoiceVersion.V1_EMO, "多情感", emotions=["开心", "悲伤", "生气", "惊讶", "激动", "冷漠", "中性"]),
    # 男声
    VoiceInfo("冷酷哥哥", "zh_male_lengkugege_emo_v2_mars_bigtts", VoiceGender.MALE, "中文",
              "冷酷帅气，有距离感，霸道", "冷酷男性、霸道角色、高冷男主",
              VoiceVersion.V1_EMO, "多情感", emotions=["生气", "冷漠", "恐惧", "开心", "厌恶", "中性", "悲伤", "沮丧"]),
    VoiceInfo("傲娇霸总", "zh_male_aojiaobazong_emo_v2_mars_bigtts", VoiceGender.MALE, "中文",
              "傲娇霸气，总裁气质，外冷内热", "霸道总裁、傲娇角色、商业精英",
              VoiceVersion.V1_EMO, "多情感", emotions=["中性", "开心", "愤怒", "厌恶"]),
    VoiceInfo("优柔公子", "zh_male_yourougongzi_emo_v2_mars_bigtts", VoiceGender.MALE, "中文",
              "温柔优雅，公子气质，略显优柔", "温柔男性、公子角色、文弱书生",
              VoiceVersion.V1_EMO, "多情感", emotions=["开心", "生气", "恐惧", "厌恶", "激动", "中性", "沮丧"]),
    VoiceInfo("儒雅男友", "zh_male_ruyayichen_emo_v2_mars_bigtts", VoiceGender.MALE, "中文",
              "儒雅温润，可靠体贴", "儒雅男友、温柔男性、稳重角色",
              VoiceVersion.V1_EMO, "多情感", emotions=["开心", "悲伤", "生气", "恐惧", "激动", "冷漠", "中性"]),
    VoiceInfo("俊朗男友", "zh_male_junlangnanyou_emo_v2_mars_bigtts", VoiceGender.MALE, "中文",
              "阳光俊朗，暖男气质", "暖男角色、阳光男友、正派男主",
              VoiceVersion.V1_EMO, "多情感", emotions=["开心", "悲伤", "生气", "惊讶", "恐惧", "中性"]),
    VoiceInfo("阳光青年", "zh_male_yangguangqingnian_emo_v2_mars_bigtts", VoiceGender.MALE, "中文",
              "阳光开朗，积极向上，青春活力", "阳光少年、热血青年、正能量角色",
              VoiceVersion.V1_EMO, "多情感", emotions=["开心", "悲伤", "生气", "恐惧", "激动", "冷漠", "中性"]),
    VoiceInfo("深夜播客", "zh_male_shenyeboke_emo_v2_mars_bigtts", VoiceGender.MALE, "中文",
              "低沉磁性，适合夜间氛围，治愈感", "播客主播、深夜电台、治愈内容",
              VoiceVersion.V1_EMO, "多情感", emotions=["惊讶", "悲伤", "中性", "厌恶", "开心", "恐惧", "激动", "沮丧", "冷漠", "生气"]),

    # ========== 三、角色扮演专用音色（部分代表性音色） ==========
    # 女性 - 年轻甜美型
    VoiceInfo("纯真少女", "ICL_zh_female_chunzhenshaonv_e588402fb8ad_tob", VoiceGender.FEMALE, "中文",
              "纯真无邪，天真烂漫", "少女角色、天真女孩、单纯角色", VoiceVersion.ROLEPLAY, "年轻甜美"),
    VoiceInfo("可爱女生", "ICL_zh_female_keainvsheng_tob", VoiceGender.FEMALE, "中文",
              "可爱甜美，讨人喜欢", "萌妹角色、可爱女孩、校园女生", VoiceVersion.ROLEPLAY, "年轻甜美"),
    VoiceInfo("病弱少女", "ICL_zh_female_bingruoshaonv_tob", VoiceGender.FEMALE, "中文",
              "声音虚弱，惹人怜爱", "病弱角色、柔弱女孩", VoiceVersion.ROLEPLAY, "年轻甜美"),
    VoiceInfo("病娇萌妹", "ICL_zh_female_bingjiaomengmei_tob", VoiceGender.FEMALE, "中文",
              "病娇属性，萌中带狠", "病娇角色、黑化萌妹", VoiceVersion.ROLEPLAY, "年轻甜美"),
    # 女性 - 成熟知性型
    VoiceInfo("知心姐姐", "ICL_zh_female_wenyinvsheng_v1_tob", VoiceGender.FEMALE, "中文",
              "温柔体贴，善解人意", "姐姐角色、知心好友、温柔女性", VoiceVersion.ROLEPLAY, "成熟知性"),
    VoiceInfo("温柔女神", "ICL_zh_female_wenrounvshen_239eff5e8ffa_tob", VoiceGender.FEMALE, "中文",
              "温柔优雅，女神气质", "女神角色、温柔女性、完美女友", VoiceVersion.ROLEPLAY, "成熟知性"),
    VoiceInfo("温柔白月光", "ICL_zh_female_yry_tob", VoiceGender.FEMALE, "中文",
              "温柔似水，白月光气质", "白月光角色、初恋", VoiceVersion.ROLEPLAY, "成熟知性"),
    # 女性 - 妖媚御姐型
    VoiceInfo("高冷御姐", "zh_female_gaolengyujie_moon_bigtts", VoiceGender.FEMALE, "中文",
              "高冷傲气，御姐气场", "御姐角色、女王、高冷女性", VoiceVersion.ROLEPLAY, "妖媚御姐"),
    VoiceInfo("妩媚御姐", "ICL_zh_female_wumeiyujie_tob", VoiceGender.FEMALE, "中文",
              "妩媚动人，御姐风范", "妩媚角色、成熟魅惑女性", VoiceVersion.ROLEPLAY, "妖媚御姐"),
    VoiceInfo("邪魅女王", "ICL_zh_female_bingjiao3_tob", VoiceGender.FEMALE, "中文",
              "邪魅霸气，女王气场", "女王角色、反派女性、邪恶角色", VoiceVersion.ROLEPLAY, "妖媚御姐"),
    VoiceInfo("傲娇女友", "ICL_zh_female_aojiaonvyou_tob", VoiceGender.FEMALE, "中文",
              "傲娇可爱，口是心非", "傲娇角色、傲娇女友", VoiceVersion.ROLEPLAY, "妖媚御姐"),
    # 男性 - 少年青年型
    VoiceInfo("阳光青年", "zh_male_yangguangqingnian_moon_bigtts", VoiceGender.MALE, "中文",
              "阳光开朗，积极向上", "阳光男主、热血少年、正派角色", VoiceVersion.ROLEPLAY, "少年青年"),
    VoiceInfo("热血少年", "ICL_zh_male_rexueshaonian_tob", VoiceGender.MALE, "中文",
              "热血沸腾，充满激情", "热血主角、战斗角色", VoiceVersion.ROLEPLAY, "少年青年"),
    VoiceInfo("元气少年", "ICL_zh_male_yuanqishaonian_tob", VoiceGender.MALE, "中文",
              "元气满满，活力四射", "元气角色、活力少年", VoiceVersion.ROLEPLAY, "少年青年"),
    # 男性 - 温柔暖男型
    VoiceInfo("温柔男友", "ICL_zh_male_wenrounanyou_tob", VoiceGender.MALE, "中文",
              "温柔体贴，呵护备至", "温柔男友、暖男角色", VoiceVersion.ROLEPLAY, "温柔暖男"),
    VoiceInfo("贴心男友", "ICL_zh_male_tiexinnanyou_tob", VoiceGender.MALE, "中文",
              "贴心呵护，善解人意", "贴心男友、理想恋人", VoiceVersion.ROLEPLAY, "温柔暖男"),
    VoiceInfo("撒娇男友", "ICL_zh_male_sajiaonanyou_tob", VoiceGender.MALE, "中文",
              "撒娇可爱，粘人小奶狗", "小奶狗角色、撒娇男友", VoiceVersion.ROLEPLAY, "温柔暖男"),
    # 男性 - 儒雅公子型
    VoiceInfo("儒雅君子", "ICL_zh_male_ruyajunzi_tob", VoiceGender.MALE, "中文",
              "儒雅端方，君子风度", "君子角色、儒雅男性", VoiceVersion.ROLEPLAY, "儒雅公子"),
    VoiceInfo("翩翩公子", "ICL_zh_male_pianpiangongzi_tob", VoiceGender.MALE, "中文",
              "风度翩翩，贵公子", "贵族公子、风流才子", VoiceVersion.ROLEPLAY, "儒雅公子"),
    VoiceInfo("仗剑侠客", "ICL_zh_male_zhangjianxiake_tob", VoiceGender.MALE, "中文",
              "仗剑天涯，侠客风范", "侠客角色、江湖人士", VoiceVersion.ROLEPLAY, "儒雅公子"),
    # 男性 - 冷酷霸气型
    VoiceInfo("冷酷哥哥", "ICL_zh_male_lengkugege_v1_tob", VoiceGender.MALE, "中文",
              "冷酷寡言，霸气侧漏", "冷酷男主、霸道角色", VoiceVersion.ROLEPLAY, "冷酷霸气"),
    VoiceInfo("霸道总裁", "ICL_zh_male_badaozongcai_v1_tob", VoiceGender.MALE, "中文",
              "霸道专横，总裁气场", "霸道总裁、商业大佬", VoiceVersion.ROLEPLAY, "冷酷霸气"),
    VoiceInfo("高冷总裁", "ICL_zh_male_gaolengzongcai_tob", VoiceGender.MALE, "中文",
              "高冷疏离，总裁范儿", "高冷总裁、冷面老板", VoiceVersion.ROLEPLAY, "冷酷霸气"),
    # 男性 - 病娇黑化型
    VoiceInfo("病娇少年", "ICL_zh_male_bingjiaoshaonian_tob", VoiceGender.MALE, "中文",
              "病娇偏执，爱到极致", "病娇角色、偏执少年", VoiceVersion.ROLEPLAY, "病娇黑化"),
    VoiceInfo("病娇男友", "ICL_zh_male_bingjiaonanyou_tob", VoiceGender.MALE, "中文",
              "病娇占有，黑化恋人", "病娇男友、黑化角色", VoiceVersion.ROLEPLAY, "病娇黑化"),
    VoiceInfo("腹黑公子", "ICL_zh_male_fuheigongzi_tob", VoiceGender.MALE, "中文",
              "腹黑心机，城府极深", "腹黑角色、心机男性", VoiceVersion.ROLEPLAY, "病娇黑化"),
    # 男性 - 成熟稳重型
    VoiceInfo("渊博小叔", "zh_male_yuanboxiaoshu_moon_bigtts", VoiceGender.MALE, "中文",
              "知识渊博，稳重可靠", "叔叔角色、成熟男性、导师", VoiceVersion.ROLEPLAY, "成熟稳重"),
    VoiceInfo("磁性男嗓", "ICL_zh_male_cixingnansang_tob", VoiceGender.MALE, "中文",
              "磁性嗓音，成熟魅力", "成熟男性、磁性嗓音", VoiceVersion.ROLEPLAY, "成熟稳重"),

    # ========== 四、特色方言口音 ==========
    VoiceInfo("呆萌川妹", "zh_female_daimengchuanmei_moon_bigtts", VoiceGender.FEMALE, "中文",
              "四川妹子，呆萌可爱", "四川角色、方言内容", VoiceVersion.DIALECT, "四川口音"),
    VoiceInfo("湾湾小何", "zh_female_wanwanxiaohe_moon_bigtts", VoiceGender.FEMALE, "中文",
              "台湾腔调，温柔软糯", "台湾角色、方言内容", VoiceVersion.DIALECT, "台湾口音"),
    VoiceInfo("北京小爷", "zh_male_beijingxiaoye_moon_bigtts", VoiceGender.MALE, "中文",
              "北京腔，痞帅味道", "北京角色、方言内容", VoiceVersion.DIALECT, "北京口音"),
    VoiceInfo("京腔侃爷", "zh_male_jingqiangkanye_moon_bigtts", VoiceGender.MALE, "中文",
              "北京话，能侃爱聊", "北京角色、侃爷类型", VoiceVersion.DIALECT, "北京口音"),
    VoiceInfo("广州德哥", "zh_male_guozhoudege_moon_bigtts", VoiceGender.MALE, "中文",
              "广州味道，大哥气质", "广东角色、方言内容", VoiceVersion.DIALECT, "广东口音"),
    VoiceInfo("粤语小溏", "zh_female_yueyunv_mars_bigtts", VoiceGender.FEMALE, "粤语",
              "粤语女声，港味十足", "粤语内容、香港角色", VoiceVersion.DIALECT, "粤语"),

    # ========== 五、英文音色（代表性） ==========
    # 美式英语
    VoiceInfo("Candice", "en_female_candice_emo_v2_mars_bigtts", VoiceGender.FEMALE, "美式英语",
              "女性，温暖亲切", "英文女性角色、温暖女性",
              VoiceVersion.ENGLISH, "美式英语", emotions=["深情", "愤怒", "ASMR", "对话/闲聊", "兴奋", "愉悦", "中性", "温暖"]),
    VoiceInfo("Glen", "en_male_glen_emo_v2_mars_bigtts", VoiceGender.MALE, "美式英语",
              "男性，成熟稳重", "英文男性角色、成熟男性",
              VoiceVersion.ENGLISH, "美式英语", emotions=["深情", "愤怒", "ASMR", "对话/闲聊", "兴奋", "愉悦", "中性", "悲伤", "温暖"]),
    VoiceInfo("Sylus", "en_male_sylus_emo_v2_mars_bigtts", VoiceGender.MALE, "美式英语",
              "男性，权威有力", "英文男性角色、权威角色",
              VoiceVersion.ENGLISH, "美式英语", emotions=["深情", "愤怒", "ASMR", "权威", "对话/闲聊", "兴奋", "愉悦", "中性", "悲伤", "温暖"]),
    # 英式英语
    VoiceInfo("Corey", "en_male_corey_emo_v2_mars_bigtts", VoiceGender.MALE, "英式英语",
              "男性，英式绅士", "英式男性角色、绅士角色",
              VoiceVersion.ENGLISH, "英式英语", emotions=["愤怒", "ASMR", "权威", "对话/闲聊", "兴奋", "愉悦", "中性", "悲伤", "温暖"]),
    VoiceInfo("Nadia", "en_female_nadia_tips_emo_v2_mars_bigtts", VoiceGender.FEMALE, "英式英语",
              "女性，英式优雅", "英式女性角色、优雅女性",
              VoiceVersion.ENGLISH, "英式英语", emotions=["深情", "愤怒", "ASMR", "对话/闲聊", "兴奋", "愉悦", "中性", "悲伤", "温暖"]),
]


# ============================================================================
# VoiceDatabase 类
# ============================================================================

class VoiceDatabase:
    """
    豆包TTS音色数据库
    
    提供两种输出格式：
    1. JSON 数组格式 - 用于程序调用
    2. Markdown 格式 - 用于 LLM 提示词
    """
    
    def __init__(self):
        self.voices = VOICE_DATA
    
    def get_voices_json(
        self,
        gender: Optional[VoiceGender] = None,
        version: Optional[VoiceVersion] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取音色列表（JSON 格式）
        
        Args:
            gender: 按性别筛选
            version: 按版本筛选
            category: 按分类筛选
            
        Returns:
            音色信息字典列表
        """
        result = []
        for voice in self.voices:
            if gender and voice.gender != gender:
                continue
            if version and voice.version != version:
                continue
            if category and voice.category != category:
                continue
            result.append(asdict(voice))
        return result
    
    def get_all_voices_json(self) -> List[Dict[str, Any]]:
        """获取所有音色（JSON 格式）"""
        return [asdict(v) for v in self.voices]
    
    def get_voices_by_gender(self, gender: str) -> List[Dict[str, Any]]:
        """按性别获取音色"""
        g = VoiceGender(gender) if isinstance(gender, str) else gender
        return self.get_voices_json(gender=g)
    
    def get_voices_by_version(self, version: str) -> List[Dict[str, Any]]:
        """按版本获取音色"""
        v = VoiceVersion(version) if isinstance(version, str) else version
        return self.get_voices_json(version=v)
    
    def get_voice_by_type(self, voice_type: str) -> Optional[Dict[str, Any]]:
        """根据 voice_type 获取单个音色"""
        for voice in self.voices:
            if voice.voice_type == voice_type:
                return asdict(voice)
        return None
    
    def search_voices(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索音色（按名称、描述、场景）"""
        keyword = keyword.lower()
        result = []
        for voice in self.voices:
            if (keyword in voice.name.lower() or
                keyword in voice.description.lower() or
                keyword in voice.scenarios.lower()):
                result.append(asdict(voice))
        return result
    
    def get_voices_markdown(self) -> str:
        """
        获取音色列表（Markdown 提示词格式）
        
        Returns:
            适用于 LLM 的 Markdown 格式文本
        """
        lines = [
            "# 豆包TTS音色数据库",
            "",
            "本文档整理了豆包语音合成的音色列表，供大模型进行角色-音色匹配使用。",
            "",
            "## 使用说明",
            "",
            "根据角色的性别、年龄、性格特点、情绪表达需求等，匹配最合适的音色。",
            "",
            "---",
            "",
        ]
        
        # 按版本分组
        version_groups = {}
        for voice in self.voices:
            key = voice.version.value
            if key not in version_groups:
                version_groups[key] = []
            version_groups[key].append(voice)
        
        version_titles = {
            "2.0": "一、通用高质量音色（2.0版本，推荐优先使用）",
            "1.0_emo": "二、多情感音色（1.0版本，支持情感控制）",
            "roleplay": "三、角色扮演专用音色",
            "dialect": "四、特色方言口音音色",
            "english": "五、英文音色",
        }
        
        for version_key, title in version_titles.items():
            if version_key not in version_groups:
                continue
            
            lines.append(f"## {title}")
            lines.append("")
            
            voices = version_groups[version_key]
            
            # 按性别分组
            female_voices = [v for v in voices if v.gender == VoiceGender.FEMALE]
            male_voices = [v for v in voices if v.gender == VoiceGender.MALE]
            
            for gender_name, gender_voices in [("女声", female_voices), ("男声", male_voices)]:
                if not gender_voices:
                    continue
                
                lines.append(f"### {gender_name}")
                lines.append("")
                
                # 表头
                if version_key == "1.0_emo":
                    lines.append("| 展示名称 | voice_type | 特点描述 | 支持情感 | 适用场景 |")
                    lines.append("|---------|-----------|---------|---------|---------|")
                else:
                    lines.append("| 展示名称 | voice_type | 特点描述 | 适用场景 |")
                    lines.append("|---------|-----------|---------|---------|")
                
                for v in gender_voices:
                    if version_key == "1.0_emo" and v.emotions:
                        emotions_str = "、".join(v.emotions[:5]) + ("..." if len(v.emotions) > 5 else "")
                        lines.append(f"| {v.name} | {v.voice_type} | {v.description} | {emotions_str} | {v.scenarios} |")
                    else:
                        lines.append(f"| {v.name} | {v.voice_type} | {v.description} | {v.scenarios} |")
                
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # 添加使用建议
        lines.extend([
            "## 使用建议",
            "",
            "### 角色匹配原则",
            "",
            "1. **性别匹配**：首先确定角色性别，选择对应的音色",
            "2. **年龄匹配**：根据角色年龄选择少年/青年/成熟/老年音色",
            "3. **性格匹配**：根据角色性格特点选择对应风格（温柔/冷酷/活泼/稳重等）",
            "4. **场景匹配**：考虑使用场景选择合适的音色类型",
            "",
            "### 推荐优先级",
            "",
            "1. **2.0版本音色**：质量最高，支持情感变化和指令遵循",
            "2. **多情感音色**：需要丰富情感表达时使用",
            "3. **角色扮演音色**：特定角色类型时使用",
            "4. **特色音色**：需要方言、IP特色时使用",
            "",
        ])
        
        return "\n".join(lines)
    
    def to_json_string(self, indent: int = 2) -> str:
        """导出为 JSON 字符串"""
        return json.dumps(self.get_all_voices_json(), ensure_ascii=False, indent=indent)


# ============================================================================
# 便捷函数
# ============================================================================

_db_instance: Optional[VoiceDatabase] = None


def get_database() -> VoiceDatabase:
    """获取数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = VoiceDatabase()
    return _db_instance


def get_voices_json(**kwargs) -> List[Dict[str, Any]]:
    """获取音色 JSON 列表"""
    return get_database().get_voices_json(**kwargs)


def get_voices_markdown() -> str:
    """获取音色 Markdown 提示词"""
    return get_database().get_voices_markdown()


# 为了向后兼容，保留原有的变量名
voice_database_prompt = get_voices_markdown()


__all__ = [
    "VoiceDatabase",
    "VoiceInfo",
    "VoiceGender",
    "VoiceVersion",
    "VOICE_DATA",
    "get_database",
    "get_voices_json",
    "get_voices_markdown",
    "voice_database_prompt",
]
