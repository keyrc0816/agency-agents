#!/usr/bin/env python3
"""Validate the zh-TW catalog metadata without mutating canonical agents."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


SCHEMA_VERSION = 1
LOCALE = "zh-TW"
AGENT_DIRS = (
    "academic", "design", "engineering", "finance", "game-development",
    "gis", "healthcare", "marketing", "paid-media", "product",
    "project-management", "research", "sales", "security",
    "spatial-computing", "specialized", "support", "testing",
)
# Characters whose simplified form is sufficiently distinctive for a hard
# validation failure. Ambiguous forms that are also legitimate Traditional
# Chinese characters (for example 後/台/里) are deliberately excluded.
HIGH_CONFIDENCE_SIMPLIFIED = frozenset(
    "这们为与业专东丝丢两严丧临义乌乐书买乱争亏亚产亲亿仅仓仪价众优伞伟传伤伦伪"
    "侠侣侥侦侨侩侪侬俩俭债倾偿储兑党兰关兴养兽冈册写军农冲决况冻净凉减凑凤凭"
    "凯击凿刍刘则刚创删刽剂剐剑剧劝办务动励劲劳势勋区医华协卖卢卫却厂厅厉压厌"
    "厕县参双变叠叶号叹听启吴呐呕员呛呜咏响哑哗哟唤啸喷喽噜团园围国图圆圣场坏"
    "块坚坛坝坠垄垒垦垫墙壮声壳壶处备够头夸夹夺奋奖妇妈妆娇娱婴孙宁宝实宠审宪"
    "宫宽宾寝对寻导寿将尔尘尝层屉届属屿岁岂岗岛岭岳峦峡崭巅币帅师帐帘帜带帮广庄"
    "庆庐库应庙庞废开异弃张弥弯弹归当录彻径忆怀态总怜恋恳恶恼悦惊惧惨惩惯愤愿"
    "慑懒戏战户执扩扫扬扰抚抛抢护报担拟拢拥拦拨择挚挛挞挟挠挡挣挥挤捞损捡换据"
    "掳掷掸掺揽搀搁搂搅携摄摆摇摊撑撵敌敛数斋斩断无旧时旷显晓暂术朴机杀杂权杆"
    "条来杨杰极构枢枣枪枫柜柠标栈栋栏树样档桥桩梦检楼欢欧残殴毁毕毙气汇汉汤沟"
    "沣沤沥沦沧沪泞泪泻泼泽洁洒浅浆浇浊测济浏浑浓涂涛涟涡涣涤润涧涨涩淀渊渍"
    "渐渔渗湾湿溃溅滚滞满滥滤滩滨潇潜澜灭灯灵灾灿炉点炼烁烂烛烟烦烧烫烬热爱爷"
    "牵牺状犹狈狞独狭狮狱猎猪猫献玛环现电画畅疗疮疯痈痉痒痪瘫瘾皑皱盏盐监盖盘"
    "睁瞒矫矿码砖砚砺砾础硕礼祷祸离秃秆种积称稳穷窃窍窑窜窝窥竖竞笃笋笔笼筑筛"
    "筹签简箩篮篱类粪粮紧纠红纤约级纪纬纯纱纲纳纵纷纸纹纺纽线练组绅细织终绊绍"
    "绎经绑绒结绕绘给络绝统绣继绩绪续绳维绵综绿缀缅缆缉编缘缚缝缠缩缴罢罗罚职"
    "联聪肃肠肤肾肿胀胁胆胜胶脉脏脑脓脚脱脸腻腾舰舱艺节芜苇苹范茎茧荆荐药莲获"
    "莹营萧萨蓝蔼蔷蚂蚕蛊蜕蝉蝇蝎衅补衬袄袜袭装见观规觅视觉览触誉计订认讥讨让训"
    "议讯记讲讳讶许讹论讼讽设访诀证评诅识诈诉诊词译试诗诚话诞询该详诧语误诱说"
    "请诸诺读课谁调谅谈谊谋谍谎谐谓谜谢谣谤谦谨谱贝贞负贡财责贤败账货质贩贪贫"
    "购贯贱贴贵贷贸费贺贼贾贿赂资赋赌赎赏赐赔赖赚赛赞赠赵赶趋跃践跷车轨轩转轮"
    "软轰轴轻载较辅辆辈辉辑输辙辞辩辫边辽达迁过迈运还进远违连迟选逊递逻遗遥邓"
    "邮邻郑郸酝酱酿释鉴钟钢钥钦钧钩钮钱钳钻铁铂铃铅铜铭银铺链销锁锅锈锋锐错锡"
    "锣锦键锻镰长门闪闭问闯闰闲间闷闸闹闻阁阅阀阐阔队阳阴阵阶际陆陈陕险随隐难"
    "雏雳雾霁静顶顷项顺须顽顾顿颁颂预领颇颈频颖颗题颜额风飘飞饭饮饲饼馆馈馋马"
    "驭驮驯驰驱驶驳驴驹驻驾骂骄验骑骗骚骤鱼鲁鲜鸟鸡鸣鸥鸭鸦鹅鹊鹏鹰麦黄齐齿龄龙"
)


class DuplicateKey(ValueError):
    pass


def object_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKey(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def parsed_field(source: str, field: str) -> str:
    """Parse the repository's simple YAML scalar, including folded continuations."""
    lines = source.removeprefix("\ufeff").splitlines()
    if not lines or lines[0].rstrip() != "---":
        return ""
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.*)$")
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip() == "---":
            break
        match = pattern.match(line)
        if not match:
            continue
        parts = [match.group(1)]
        for continuation in lines[index + 1:]:
            if continuation.rstrip() == "---" or not re.match(r"^\s+\S", continuation):
                break
            parts.append(continuation.strip())
        value = " ".join(parts).strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value[1:-1]
        if len(value) >= 2 and value[0] == value[-1] == "'":
            return value[1:-1].replace("''", "'")
        return value
    return ""


def canonical_agents(root: Path) -> dict[str, tuple[str, str]]:
    agents: dict[str, tuple[str, str]] = {}
    for directory in AGENT_DIRS:
        for path in sorted((root / directory).rglob("*.md")):
            source = path.read_text(encoding="utf-8-sig")
            name = parsed_field(source, "name")
            if not name:
                continue
            slug = path.stem
            if slug in agents:
                raise ValueError(f"duplicate canonical slug: {slug}")
            agents[slug] = (name, parsed_field(source, "description"))
    return agents


def owner_review_slugs(path: Path) -> list[str]:
    if not path.exists():
        return []
    report = path.read_text(encoding="utf-8")
    marker = "The following entries remain Owner review exceptions"
    if marker not in report:
        return []
    exception_section = report.split(marker, 1)[1].split("Current QA state", 1)[0]
    return re.findall(r"^- `([^`]+)`", exception_section, re.MULTILINE)


def print_section(title: str, items: list[str]) -> None:
    print(f"{title}: {len(items)}")
    for item in items:
        print(f"  - {item}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--resource", type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    resource = args.resource or root / "scripts/i18n/agent-metadata-zh-TW.json"
    review_path = root / "scripts/i18n/agent-metadata-zh-TW-owner-review.md"

    errors: list[str] = []
    warnings: list[str] = []
    try:
        resource_bytes = resource.read_bytes()
        data = json.loads(resource_bytes.decode("utf-8"), object_pairs_hook=object_no_duplicates)
    except (OSError, json.JSONDecodeError, DuplicateKey) as exc:
        print(f"Localization schema error: {exc}", file=sys.stderr)
        return 1

    if data.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if data.get("locale") != LOCALE:
        errors.append(f"locale must be {LOCALE}")
    association_path = resource.parent / "source-association.json"
    try:
        association = json.loads(association_path.read_text(encoding="utf-8"))
        if association.get("schemaVersion") != 1:
            errors.append("source association schemaVersion must be 1")
        if association.get("sourceBaselineCommit") != "3c9588880b7cafaec325a104899fd8bbe27e7d72":
            errors.append("source association baseline commit does not match the approved pin")
        if association.get("sourceDefaultRef") != "main":
            errors.append("source association sourceDefaultRef must be the durable main ref")
        if "sourceBranch" in association:
            errors.append("source association must not depend on a permanent feature branch")
        if association.get("resourcePath") != "scripts/i18n/agent-metadata-zh-TW.json":
            errors.append("source association resourcePath is invalid")
        if association.get("resourceSha256") != hashlib.sha256(resource_bytes).hexdigest():
            errors.append("source association resourceSha256 does not match the resource")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"source association is missing or malformed: {exc}")
    mappings = data.get("agents")
    if not isinstance(mappings, dict):
        print("Localization schema error: agents must be an object", file=sys.stderr)
        return 1

    try:
        canonical = canonical_agents(root)
    except (OSError, ValueError) as exc:
        print(f"Canonical catalog error: {exc}", file=sys.stderr)
        return 1

    missing = sorted(set(canonical) - set(mappings))
    orphaned = sorted(set(mappings) - set(canonical))
    stale: list[str] = []
    localized_names: list[str] = []
    if list(mappings) != sorted(mappings):
        errors.append("agents keys must be sorted by canonical slug")

    required = {"sourceName", "sourceDescriptionSha256", "name", "description"}
    for slug in sorted(set(canonical) & set(mappings)):
        entry = mappings[slug]
        if not isinstance(entry, dict) or set(entry) != required:
            errors.append(f"{slug}: entry must contain exactly {sorted(required)}")
            continue
        source_name, source_description = canonical[slug]
        expected_hash = hashlib.sha256(source_description.encode("utf-8")).hexdigest()
        if entry["sourceName"] != source_name or entry["sourceDescriptionSha256"] != expected_hash:
            stale.append(slug)
        for field in ("sourceName", "sourceDescriptionSha256", "name", "description"):
            value = entry[field]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{slug}.{field}: must be a non-empty string")
                continue
            if value != value.strip():
                errors.append(f"{slug}.{field}: leading/trailing whitespace is forbidden")
            if "\n" in value or "\r" in value:
                errors.append(f"{slug}.{field}: newlines are forbidden")
            if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
                errors.append(f"{slug}.{field}: control characters are forbidden")
        for field in ("name", "description"):
            simplified = sorted(set(entry[field]) & HIGH_CONFIDENCE_SIMPLIFIED)
            if simplified:
                errors.append(f"{slug}.{field}: high-confidence Simplified Chinese: {''.join(simplified)}")
        if "中文：" in entry["description"]:
            errors.append(f"{slug}.description: localized value must not contain the display prefix 中文：")
        localized_names.append(entry["name"])

    duplicates = sorted(name for name, count in Counter(localized_names).items() if count > 1)
    warnings.extend(f"duplicate zh-TW name: {name}" for name in duplicates)
    qa_review = owner_review_slugs(review_path)

    print_section("Missing zh-TW translations", missing)
    print_section("Stale zh-TW translations", stale)
    print_section("Orphaned zh-TW translations", orphaned)
    print_section("Ambiguous / QA-review translations", qa_review)
    print_section("Warnings", warnings)
    print_section("Schema errors", errors)
    print(f"Validated canonical agents: {len(canonical)}")
    print(f"Validated zh-TW mappings: {len(mappings)}")
    return 1 if missing or stale or orphaned or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
