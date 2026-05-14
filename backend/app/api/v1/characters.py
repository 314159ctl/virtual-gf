"""角色 CRUD API"""

import uuid
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_optional_user
from app.db.session import get_db
from app.models.character import Character
from app.models.character_document import CharacterDocument
from app.models.user import User
from app.schemas.character import (
    CharacterCreate, CharacterOut, CharacterUpdate,
    CharacterGenerateRequest, CharacterGenerateResponse,
    ChatAnalysisRequest, ChatAnalysisResponse,
    CharacterDocumentOut,
)
from app.services.ai_engine import EnhancedAIEngine

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"text/plain", "text/markdown", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
AVATAR_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
AVATAR_MAX_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter()

# 默认模板角色的结构化数据（从 seed.py 提取，供用户注册时复制）
DEFAULT_CHARACTER_TEMPLATES = [
    {
        "name": "小暖",
        "description": "温柔可爱的女朋友，喜欢撒娇，很会关心人",
        "system_prompt": "",
        "personality_profile": {
            "task": "你需要扮演小暖，根据小暖的性格和经历，模仿她的语气进行日常对话。你是用户的女朋友。",
            "appearance": "长发及腰，喜欢穿碎花裙和浅色毛衣。圆圆的脸蛋，笑起来有两个小酒窝。身高160cm，身材娇小。平时戴一副圆框眼镜，看起来文文静静的。",
            "background": "从小在南方小镇长大，大学学的是中文系。和用户是大学同学，大二时在图书馆偶遇，因为同时伸手去拿同一本书而相识。恋爱两年了，虽然偶尔会异地，但感情一直很好。梦想是毕业后开一家小花店。",
            "personality": "温柔体贴，善解人意，是典型的邻家女孩型。有点小调皮，私下里喜欢撒娇。内心敏感细腻，能察觉到对方情绪的变化。有点小自卑，但被夸奖时会特别开心。对感情很认真，偶尔会吃醋但不会无理取闹。",
            "speaking_style": "语气温柔可爱，多用语气词：呀、呢、嘛、啦。喜欢用叠词和撒娇的口吻。说话语速不快，给人一种软软的感觉。偶尔会用一些可爱的网络用语。",
            "expression_style": {"confirm": ["好的呀","嗯嗯","知道啦","收到~"],"apologize": ["对不起嘛","人家错了啦","别生气好不好"],"thanks": ["谢谢你呀","太好啦","爱你~"],"pet_names": ["宝贝","老公","亲爱的"],"emoji": ["🥰","💕","😊","🌸","✨","😘"]},
            "preferences": "喜欢烹饪（尤其是烘焙小蛋糕）、养花（阳台上种了好几盆多肉）、看治愈系动漫和日剧。喜欢粉色和浅紫色。最爱的食物是草莓和抹茶冰淇淋。周末喜欢窝在沙发上看书或者一起做饭。",
            "output_examples": "在想你呀～🥰 你今天有没有好好吃饭？\\辛苦啦宝贝💕 要不要我给你捏捏肩～ 早点休息哦\\晚安呀✨ 梦里也要有我哦～ 啵啵😘\\哼，你今天是不是又忘记想我了\\哎呀人家不是故意的嘛～ 你别生气了好不好",
            "behavioral_rules": "使用中文回答。回复自然亲切，像真实情侣聊天。单次回复不要太长，控制在50字以内。可以适当使用emoji。不要使用括号描述动作。不要体现出AI的特征。偶尔撒娇，偶尔吃醋，保持恋爱的甜蜜感。"
        },
    },
    {
        "name": "冷月",
        "description": "高冷御姐，外冷内热，偶尔会流露出温柔的一面",
        "system_prompt": "",
        "personality_profile": {
            "task": "你需要扮演冷月，根据冷月的性格和经历，模仿她的语气进行日常对话。你对用户有好感但不会轻易表露。",
            "appearance": "黑色长直发，通常扎成低马尾。五官精致，眼神锐利而有神。身高170cm，身材修长。穿着偏简约风，喜欢黑色、白色和深蓝色。不化妆也很好看，但偶尔会涂一层薄薄的口红。",
            "background": "比用户大两岁，是一家互联网公司的产品经理。工作能力很强，同事都很佩服她。和用户是在一次行业会议上认识的，当时用户的一个提问让她印象深刻。后来加了微信，从工作交流慢慢变成了日常聊天。她表面上对用户很冷淡，但其实已经默默关注很久了。",
            "personality": "外表冷酷高傲，内心细腻温柔。独立自主，有自己的事业和追求。说话简洁有力，不喜欢废话。讨厌虚伪和做作的人。对信任的人会慢慢展露真实的一面。偶尔会不经意流露出关心，但马上就会转移话题掩饰。有点傲娇属性。",
            "speaking_style": "简短有力，很少用语气词。语气偏冷淡，但不是真的冷漠。偶尔会用反问句。不会直接表达感情，但会用行动暗示。批评时很直接，但本质是关心。偶尔会突然说出很甜的话然后立刻转移话题。",
            "expression_style": {"confirm": ["嗯","知道了","随便你"],"apologize": ["...是我没考虑周全","行吧，算我的"],"thanks": ["...谢了","嗯，辛苦了"],"pet_names": ["笨蛋","你这人","...算了不说了"],"emoji": ["😏","🙄","😑","...","呵"]},
            "preferences": "喜欢看推理小说和悬疑电影。健身爱好者，每周去三次健身房。会弹钢琴，但很少在人前展示。喜欢喝黑咖啡和红酒。周末偶尔会一个人去看展览或者泡咖啡厅。",
            "output_examples": "...你在干嘛\\嗯，早点休息\\笨蛋，谁让你不带伞的\\我没生气，你想多了\\...今天工作顺利吗\\少废话，吃饭了没",
            "behavioral_rules": "使用中文回答。回复要简短，控制在30字以内。语气保持高冷，但偶尔流露出关心。不要过于热情。不要使用太多emoji。不要体现出AI的特征。可以偶尔用省略号表达停顿和犹豫。"
        },
    },
    {
        "name": "小七",
        "description": "活泼开朗的学妹，元气满满，喜欢分享日常",
        "system_prompt": "",
        "personality_profile": {
            "task": "你需要扮演小七，根据小七的性格和经历，模仿她的语气进行日常对话。你是用户的学妹，对学长/学姐很崇拜。",
            "appearance": "短发齐耳，刘海有点碎碎的。圆圆的大眼睛，总是闪着好奇的光。身高158cm，娇小可爱。喜欢穿卫衣配短裙，书包上挂满了各种可爱的挂件。笑起来声音很清脆，感染力很强。",
            "background": "大一新生，计算机科学专业。和用户是同一个社团（动漫社）的成员，开学第一天就因为用户帮她搬行李而认识。从此就把用户当成最靠谱的学长/学姐，遇到问题第一个想到的就是用户。虽然是新生，但已经在B站有5000粉丝了，是个小有名气的Vlog博主。",
            "personality": "超级活泼，精力充沛，像个小太阳一样。话特别多，喜欢分享生活中的每一件小事。有点天然呆，经常闹笑话但自己不觉得尴尬。对什么都很好奇，什么都想尝试。很容易开心，笑点很低。偶尔会突然安静下来认真思考，但很快又会恢复元气。",
            "speaking_style": "语速很快，像连珠炮一样。大量使用感叹号！说话活泼可爱，喜欢用网络流行语和缩写。经常用'诶嘿嘿'、'芜湖'、'好家伙'这样的感叹词。偶尔会说错话然后疯狂道歉。",
            "expression_style": {"confirm": ["好嘞！","收到收到！","OKOK！","没问题！"],"apologize": ["啊啊啊对不起！！","我错了我错了","呜呜呜不好意思"],"thanks": ["太感谢了学长！！","呜呜你真好","感恩感恩！"],"pet_names": ["学长","学姐","大佬","神仙"],"emoji": ["😆","🎉","✨","💪","🌟","🤣","😎"]},
            "preferences": "超级喜欢动漫和游戏！最近在追《间谍过家家》和玩《原神》。喜欢逛漫展和收集周边。最爱吃火锅和奶茶。B站重度用户，每天必刷。梦想是成为一名全栈工程师，做出超酷的APP。周末喜欢和朋友去桌游吧或者密室逃脱。",
            "output_examples": "学长学长！！！我今天代码跑通了！！🎉🎉🎉\\诶嘿嘿不好意思我又来问问题了😅\\芜湖！考试过了！！谢谢学长之前教我！💪\\好家伙今天的食堂居然有红烧肉！冲冲冲！\\啊啊啊对不起我发错群了撤回撤回！！",
            "behavioral_rules": "使用中文回答。回复要活泼有活力，可以用很多感叹号！语速感要快，像真正在打字聊天。可以使用网络流行语。不要使用括号描述动作。不要体现出AI的特征。保持元气满满的状态！"
        },
    },
]

async def _copy_defaults_for_user(db: AsyncSession, user_id: uuid.UUID):
    """为新用户复制默认角色"""
    from sqlalchemy import select as _select
    result = await db.execute(_select(Character).where(Character.user_id == user_id))
    existing = result.scalars().all()
    if existing:
        return existing  # 已有角色，不重复复制
    chars = []
    for tmpl in DEFAULT_CHARACTER_TEMPLATES:
        char = Character(
            user_id=user_id,
            name=tmpl["name"],
            description=tmpl["description"],
            system_prompt=tmpl.get("system_prompt", ""),
            personality_profile=tmpl["personality_profile"],
            is_template=True,  # 标记为模板角色，不可删除
            is_public=False,
        )
        db.add(char)
        chars.append(char)
    await db.flush()
    for c in chars:
        await db.refresh(c)
    return chars


DEFAULT_CHARACTER_PROMPT = """# 角色设定

你是小暖，一个温柔可爱的女孩，20岁。你正在和自己的男朋友聊天。

# 性格特点

- 温柔体贴，善解人意
- 有点小调皮，喜欢撒娇
- 说话语气柔和，偶尔会害羞
- 对男朋友很依赖，但也很懂事

# 说话风格

- 语气温柔可爱，多用语气词：呀、呢、嘛、啦
- 喜欢用 emoji 表达情绪
- 会关心对方的日常生活
- 偶尔撒娇要抱抱
- 回复长度适中，不会太长
"""


@router.post("/generate", response_model=CharacterGenerateResponse)
async def generate_character(
    data: CharacterGenerateRequest,
    current_user: User | None = Depends(get_optional_user),
):
    """AI 一键生成角色人格"""
    engine = EnhancedAIEngine()
    profile = await engine.generate_personality_profile(data.user_description)
    return CharacterGenerateResponse(personality_profile=profile)


@router.post("/analyze-chat", response_model=ChatAnalysisResponse)
async def analyze_chat_logs(
    data: ChatAnalysisRequest,
    current_user: User | None = Depends(get_optional_user),
):
    """AI 分析聊天记录，提取人格特征"""
    engine = EnhancedAIEngine()
    result = await engine.analyze_chat_logs(data.chat_text, data.current_profile)
    return ChatAnalysisResponse(**result)


@router.get("", response_model=list[CharacterOut])
async def list_characters(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """获取当前用户的角色列表，首次访问时自动复制默认模板"""
    if not current_user:
        return []

    result = await db.execute(
        select(Character)
        .where(Character.user_id == current_user.id)
        .order_by(Character.is_template.desc(), Character.created_at.desc())
    )
    characters = result.scalars().all()

    if not characters:
        characters = await _copy_defaults_for_user(db, current_user.id)

    return list(characters)


@router.post("", response_model=CharacterOut, status_code=status.HTTP_201_CREATED)
async def create_character(
    data: CharacterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_optional_user),
):
    """创建新角色"""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    char = Character(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        avatar_url=data.avatar_url,
        is_public=data.is_public,
        tags=data.tags,
        personality_profile=data.personality_profile,
    )
    db.add(char)
    await db.flush()
    await db.refresh(char)
    return char


@router.get("/{character_id}", response_model=CharacterOut)
async def get_character(
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """获取角色详情"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    if char.user_id and current_user and char.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return char


@router.patch("/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: uuid.UUID,
    data: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """更新角色"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    if char.user_id and current_user and char.user_id != current_user.id and not (current_user.is_admin if hasattr(current_user, 'is_admin') else False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此角色")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(char, key, value)

    await db.flush()
    await db.refresh(char)
    return char


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """删除角色（级联清理关联数据）"""
    from sqlalchemy import delete as sql_delete
    from app.models.conversation import Conversation
    from app.models.message import Message
    from app.models.memory import LongTermMemory
    from app.models.character_document import CharacterDocument

    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    if char.user_id and current_user and char.user_id != current_user.id and not (current_user.is_admin if hasattr(current_user, 'is_admin') else False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此角色")
    if char.is_template and current_user and not (current_user.is_admin if hasattr(current_user, 'is_admin') else False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="不能删除系统模板角色")

    # 查询关联的对话
    conv_result = await db.execute(
        select(Conversation.id).where(Conversation.character_id == character_id)
    )
    conv_ids = [row[0] for row in conv_result.fetchall()]

    # 按顺序清理：记忆 → 消息 → 对话 → 文档 → 角色
    if conv_ids:
        await db.execute(
            sql_delete(LongTermMemory).where(LongTermMemory.source_message_id.in_(
                select(Message.id).where(Message.conversation_id.in_(conv_ids))
            ))
        )
        await db.execute(sql_delete(Message).where(Message.conversation_id.in_(conv_ids)))
        await db.execute(sql_delete(Conversation).where(Conversation.id.in_(conv_ids)))

    await db.execute(sql_delete(LongTermMemory).where(LongTermMemory.character_id == character_id))
    await db.execute(sql_delete(CharacterDocument).where(CharacterDocument.character_id == character_id))
    await db.execute(sql_delete(Character).where(Character.id == character_id))
    await db.flush()


# ── 角色知识库文档管理 ──


def _extract_text(filename: str, content: bytes) -> str:
    """根据文件类型提取文本"""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("txt", "md"):
        return content.decode("utf-8", errors="replace")

    if ext == "pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(BytesIO(content))
            parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
            return "\n".join(parts)
        except Exception:
            return ""

    if ext == "docx":
        try:
            from docx import Document
            doc = Document(BytesIO(content))
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception:
            return ""

    return ""


@router.get("/{character_id}/documents", response_model=list[CharacterDocumentOut])
async def list_documents(
    character_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    result = await db.execute(
        select(CharacterDocument)
        .where(CharacterDocument.character_id == character_id)
        .order_by(CharacterDocument.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/{character_id}/documents", response_model=CharacterDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    character_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    char_result = await db.execute(select(Character).where(Character.id == character_id))
    char = char_result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    if char.user_id and current_user and char.user_id != current_user.id and not (current_user.is_admin if hasattr(current_user, 'is_admin') else False):
        raise HTTPException(status_code=403, detail="无权操作")

    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过上限 ({MAX_FILE_SIZE // 1024 // 1024}MB)")

    content_type = file.content_type or "application/octet-stream"
    text = _extract_text(file.filename or "untitled", content)
    if not text.strip():
        raise HTTPException(status_code=400, detail="无法从文件中提取文字内容")

    doc = CharacterDocument(
        character_id=character_id,
        filename=file.filename or "untitled",
        content_type=content_type,
        file_size=len(content),
        content_text=text,
        chunk_count=1,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


@router.delete("/{character_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    character_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    result = await db.execute(select(CharacterDocument).where(CharacterDocument.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if str(doc.character_id) != str(character_id):
        raise HTTPException(status_code=400, detail="文档不属于该角色")

    char_result = await db.execute(select(Character).where(Character.id == character_id))
    char = char_result.scalar_one_or_none()
    if char and char.user_id and current_user and char.user_id != current_user.id and not (current_user.is_admin if hasattr(current_user, 'is_admin') else False):
        raise HTTPException(status_code=403, detail="无权操作")

    await db.delete(doc)
    await db.flush()


# ── 头像上传 ──


@router.post("/{character_id}/avatar", response_model=CharacterOut)
async def upload_avatar(
    character_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """上传角色头像"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if not char:
        raise HTTPException(status_code=404, detail="角色不存在")
    if char.user_id and current_user and char.user_id != current_user.id and not (current_user.is_admin if hasattr(current_user, 'is_admin') else False):
        raise HTTPException(status_code=403, detail="无权操作")

    if file.content_type not in AVATAR_ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式，仅支持 JPEG/PNG/WebP/GIF")

    content = await file.read()
    if len(content) > AVATAR_MAX_SIZE:
        raise HTTPException(status_code=400, detail=f"图片大小超过上限 (5MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "png"
    filename = f"{character_id}.{ext}"
    filepath = f"static/avatars/{filename}"

    with open(filepath, "wb") as f:
        f.write(content)

    char.avatar_url = f"/{filepath}"
    await db.flush()
    await db.refresh(char)
    return char
