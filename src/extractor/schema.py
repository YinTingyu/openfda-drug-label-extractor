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
        "Absolute prohibitions — whom the product must not be used on, and where or how it must not be applied. (e.g. known allergy "
        "to an ingredient, a disease that rules it out). "
        "Specific uses ruled out within its intended route "
        "(e.g. 'do not use in the eyes', 'not for injection'). "
        "Usually found in CONTRAINDICATIONS (Rx) or DO_NOT_USE (OTC), but "
        "those sections also contain packaging, tamper-seal, storage and "
        "handling text, which must be excluded. "
        "Empty list if the label states none."
        ),
    )
    cautions: list[str] = Field(  # 第二级：慎用，需要咨询医生
        default_factory=list,  # 默认空列表
        description=(
            "Conditions under which the user should consult a professional "
            "before use — pregnancy, nursing, an existing condition or wound "
            "type. Usually from ASK_DOCTOR. Not absolute bans, not outcomes, "
            "and not warnings that apply to the whole product class. "
            "Each item must be a complete, independently understandable "
            "condition. Empty list if none."
        ),
    )

    general_warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Standard warnings that apply to the product class rather than to "
            "any particular user or condition — 'for external use only', "
            "'keep out of reach of children'. Empty list if none."
        ),
    )

    adverse_reactions: list[str] = Field(
        default_factory=list,  # 默认空列表
        description=(
            "Possible harmful effects of using the product (e.g. anaphylaxis, Stevens-Johnson syndrome, ocular burning)."
            "These describe outcomes, not conditions of use. "
            "Empty list if none."
        ),
    )

    stop_use_conditions: list[str] = Field(  # 第三级：出现某情况时停药
        default_factory=list,  # 默认空列表
        description=(
            "Situations in which the user should discontinue use. "
            "Each item must be independently understandable. Empty list if none."
        ),
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
        default_factory=SafetyInfo,  # 默认空的 SafetyInfo
        description=(
            "Safety statements from the label. Across all safety fields, exclude "
            "text about the container or storage — tamper seals, closing the cap, "
            "storage temperature — wherever it appears, including inside "
            "DO_NOT_USE or WARNINGS sections."
        ),
    )
    dosage_form: Optional[DosageForm] = Field(  # 剂型：只能是 DosageForm 里的值，或 None
        default=None,  # 标签没写时为 None
        description=("Physical form of the product as administered, taken from dosage or "  # 让模型从用法里判断剂型
        "administration text (e.g. 'dissolve under the tongue' pellets => pellet). "
        "Not the plant part or raw ingredient. "
        "Physical dosage form. Apply the first rule that matches: "
        "1. Ophthalmic products administered as drops ('instill one to two "
        "drops') => 'drops', even when the product is also called a solution."
        "2. A form word stated for the product itself ('4 or 6 Pellets', "
        "'Powder', 'ophthalmic solution') => that word."
        "3. No form word stated => infer from how it is administered: "
        "'dissolve under the tongue' => 'pellet'; 'spray a small amount "
        "on the area' => 'spray'."
        "4. Otherwise null. Never infer from ingredients, packaging or "
        "product name."
        "Null if not stated.")
    )


