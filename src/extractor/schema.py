from typing import Literal, Optional   # Literal 限定只能取几个固定值；Optional[X] 表示 X 或 None
from pydantic import BaseModel, Field  # BaseModel 定义数据结构；Field 给字段加默认值和描述

# Schema 的结构对应 FDA 标签里安全信息的分级，
# 让模型每类信息都有地方放，而不是全部塞进一个列表

# 允许的剂型：模型只能从这里选，避免出现 "Pellets" / "Bark" / "ophthalmic solution" 这种五花八门的写法
DosageForm = Literal[
    "tablet", "capsule", "pellet", "powder", "liquid", "solution", "suspension",  # 片剂、胶囊、小丸、粉剂、液体、溶液、混悬液
    "syrup", "cream", "ointment", "gel", "lotion", "spray", "drops",             # 糖浆、乳膏、软膏、凝胶、洗剂、喷雾、滴剂
    "injection", "patch", "suppository", "other",                                # 注射剂、贴剂、栓剂、其他
]

class SafetyInfo(BaseModel):  # 安全信息，分三级
    contraindications: list[str] = Field(
        default_factory=list, description=(
        "Absolute prohibitions concerning the patient's body or medical "
        "condition — who must never use this product (e.g. known allergy "
        "to an ingredient, a disease that rules it out). "
        "Usually found in CONTRAINDICATIONS (Rx) or DO_NOT_USE (OTC), but "
        "those sections also contain packaging, tamper-seal, storage and "
        "handling text, which must be excluded. "
        "Empty list if the label states none."
        ),
    )
    cautions: list[str] = Field(  # 第二级：慎用，需要咨询医生
        default_factory=list,  # 默认空列表
        description="Conditions requiring care or a doctor's advice before use "  # 给模型的说明
        "(ASK_DOCTOR, WARNINGS), e.g. pregnancy or breast-feeding, liver disease.",
    )
    stop_use_conditions: list[str] = Field(  # 第三级：出现某情况时停药
        default_factory=list,  # 默认空列表
        description="Situations in which the user should stop taking the drug "  # 给模型的说明
        "(STOP_USE), e.g. symptoms persist more than N days.",
    )

class DrugLabel(BaseModel):  # 模型最终要返回的完整结构
    indications: list[str] = Field(  # 适应症
        default_factory=list,  # 默认空列表
        description=(  # 给模型一条明确的决策规则，消除“这句算不算适应症”的歧义
            "Specific medical conditions or symptoms this product treats or relieves. "  # 要什么：具体的病症或症状
            "Look in INDICATIONS_AND_USAGE and PURPOSE sections. "  # 去哪找：告诉模型看哪两个段落
            "Exclude non-informative phrases such as 'condition listed above' or "  # 不要什么：没有信息量的套话
            "'as directed by the physician'. "
            "Each item must be an independently meaningful condition "  # 每一项单独拿出来也要有意义
            "(e.g. 'acne', not 'temporary relief')."  # 正反例各一个，比抽象规则更好用
        ),
    )
    safety: SafetyInfo = Field(  # 嵌套上面定义的 SafetyInfo
        description="Safety statements about the patient. Never include packaging, tamper "  # 明确排除包装、封口、储存等非人体相关信息
        "seals, storage, 'external use only', or 'keep out of reach of children'.",
    )
    dosage_form: Optional[DosageForm] = Field(  # 剂型：只能是 DosageForm 里的值，或 None
        default=None,  # 标签没写时为 None
        description="Physical form of the product as administered, taken from dosage or "  # 让模型从用法里判断剂型
        "administration text (e.g. 'dissolve under the tongue' pellets => pellet). "
        "Not the plant part or raw ingredient. Null if not stated.",  # 防止把原料部位（如 BARK 树皮）当成剂型
    )


