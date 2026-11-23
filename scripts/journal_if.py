# -*- coding: utf-8 -*-
"""
期刊影响因子参考表（2024 JCR 公开数据整理，近似参考值，仅用于排序与筛选）
匹配方式：规范化后精确匹配（不做模糊包含匹配，避免 Nature Sustainability / Sustainability 混淆）
"""

JOURNAL_IF = {
    # ---------- 综合 / 材料顶级 ----------
    "nature": 50.5, "science": 44.7, "nature materials": 37.2,
    "nature reviews materials": 79.8, "nature nanotechnology": 38.1,
    "nature communications": 14.7, "nature sustainability": 25.7,
    "nature reviews physics": 36.6, "nature physics": 17.6,
    "nature chemistry": 19.2, "nature reviews chemistry": 34.1,
    "science advances": 11.7, "science robotics": 26.1,
    "proceedings of the national academy of sciences of the united states of america": 9.4,
    "national science review": 16.3, "science bulletin": 18.8,
    "the innovation": 33.2, "nature protocols": 13.1,
    "scientific reports": 3.8, "matter": 17.3, "chem": 19.1, "joule": 38.6,
    "cell reports physical science": 7.3, "device": 8.0, "patterns": 6.0,
    "nature communications materials": 12.0, "npj materials degradation": 4.0,

    # ---------- 材料类 ----------
    "advanced materials": 27.4, "advanced functional materials": 18.5,
    "advanced science": 14.3, "advanced engineering materials": 3.9,
    "advanced materials interfaces": 4.3, "advanced materials technologies": 6.4,
    "advanced composites and hybrid materials": 23.0,
    "progress in materials science": 33.6,
    "materials science and engineering r reports": 27.3,
    "materials today": 17.3, "materials today physics": 10.6,
    "materials today chemistry": 8.0, "materials today advances": 8.4,
    "materials today communications": 3.7, "applied materials today": 7.2,
    "materials horizons": 12.3, "journal of materials chemistry a": 10.7,
    "journal of materials science and technology": 11.2,
    "acta materialia": 8.3, "scripta materialia": 5.3,
    "composites part b engineering": 12.7,
    "composites science and technology": 8.3,
    "composites part a applied science and manufacturing": 7.7,
    "composite structures": 6.3, "composites communications": 6.5,
    "acs nano": 15.8, "acs applied materials and interfaces": 8.3,
    "acs applied nano materials": 5.5, "acs applied polymer materials": 4.4,
    "nano letters": 9.6, "nano energy": 16.9, "nanoscale": 5.8,
    "small": 13.0, "small methods": 10.7, "small science": 9.7,
    "carbon": 10.5, "2d materials": 5.2, "nanotechnology": 3.9,
    "chemical engineering journal": 13.3, "chemical science": 7.6,
    "journal of the american chemical society": 14.4,
    "angewandte chemie international edition": 16.1,
    "advanced powder materials": 21.1, "journal of advanced ceramics": 16.9,
    "journal of the european ceramic society": 5.7, "ceramics international": 5.1,
    "journal of alloys and compounds": 5.8,
    "journal of materials research and technology": 6.2,
    "materials and design": 7.6, "materials characterization": 4.8,
    "materials chemistry and physics": 4.3, "journal of materials science": 3.5,
    "rare metals": 8.8, "journal of magnesium and alloys": 15.8,
    "journal of materials processing technology": 6.7,
    "additive manufacturing": 10.3, "virtual and physical prototyping": 10.2,
    "international journal of plasticity": 9.4,
    "journal of the mechanics and physics of solids": 5.9,
    "extreme mechanics letters": 4.5, "nano materials science": 9.6,
    "materials research letters": 8.6, "journal of materiomics": 8.4,
    "materials futures": 12.9, "interdisciplinary materials": 24.5,
    "rare metal materials and engineering": 4.1,
    "transactions of nonferrous metals society of china": 4.5,
    "acta metallurgica sinica": 2.0,
    "journal of iron and steel research international": 2.9,
    "science china technological sciences": 4.2,
    "international journal of minerals metallurgy and materials": 5.6,
    "journal of central south university": 3.9,
    "journal of materials engineering and performance": 1.9,
    "metals": 2.6, "materials": 3.1, "coatings": 2.9, "nanomaterials": 4.4,
    "molecules": 4.2, "polymers": 4.7, "sustainability": 3.3, "chemistry": 3.0,
    "lubricants": 2.9, "applied sciences basel": 2.5, "processes": 2.8,
    "materials today proceedings": 1.0, "materials today sustainability": 7.9,
    "journal of materials science materials in medicine": 3.5,

    # ---------- 表面 / 涂层 / 摩擦学核心 ----------
    "applied surface science": 6.3, "surface and coatings technology": 5.4,
    "surface science reports": 9.2, "surfaces and interfaces": 5.7,
    "applied surface science advances": 8.0,
    "tribology international": 6.1, "wear": 6.1, "friction": 6.3,
    "tribology letters": 3.4, "tribology transactions": 2.0,
    "journal of tribology": 2.5, "lubrication science": 1.8,
    "tribology materials surfaces and interfaces": 2.0,
    "industrial lubrication and tribology": 1.6,
    "proceedings of the institution of mechanical engineers part j journal of engineering tribology": 1.8,
    "diamond and related materials": 4.3, "thin solid films": 2.0,
    "journal of colloid and interface science": 9.4, "langmuir": 3.7,
    "colloids and surfaces a physicochemical and engineering aspects": 4.9,
    "soft matter": 2.9, "acs sustainable chemistry and engineering": 7.1,
    "green chemistry": 9.3, "chemical engineering science": 4.1,
    "international journal of mechanical sciences": 7.1,
    "mechanical systems and signal processing": 7.9,
    "engineering failure analysis": 4.4,
    "journal of manufacturing processes": 6.1,
    "international journal of refractory metals and hard materials": 4.2,
    "international journal of machine tools and manufacture": 8.7,
    "corrosion science": 7.4, "journal of cleaner production": 9.7,
    "science of the total environment": 8.2,
    "environmental science and technology": 10.8,
    "atmospheric environment": 4.2, "environmental pollution": 7.6,
    "journal of hazardous materials": 12.2,
    "environmental science and technology letters": 10.9,
    "chemical reviews": 51.4, "chemical society reviews": 40.4,
    "progress in polymer science": 26.0, "progress in organic coatings": 6.5,
    "polymer": 4.1, "polymer composites": 4.8, "polymer testing": 5.0,
    "journal of applied polymer science": 2.7,
    "journal of vinyl and additive technology": 2.9,
    "tribology international reports": 2.0,
    "construction and building materials": 7.4,
    "cement and concrete composites": 10.8, "cement and concrete research": 10.9,
    "engineering structures": 5.6, "energy": 9.0, "applied energy": 10.1,
    "renewable and sustainable energy reviews": 16.3,
    "journal of molecular liquids": 5.3,
    "journal of industrial and engineering chemistry": 5.5,
    "separation and purification technology": 8.1,
    "advanced materials research": 0.5, "key engineering materials": 0.4,
    "materials science forum": 0.4,
    "journal of bio and tribo corrosion": 2.1,
    "journal of engineering materials and technology": 1.7,
    "international journal of advanced manufacturing technology": 2.9,
    "journal of materials science and technology advances": 3.0,

    # ---------- 塑性变形 / 金属材料核心刊（2024 JCR 近似值） ----------
    "materials science and engineering a": 7.0,
    "materials science and engineering b": 4.2,
    "materials science and engineering": 2.0,
    "metallurgical and materials transactions a": 2.6,
    "metallurgical and materials transactions b": 2.3,
    "materials letters": 2.7,
    "materials transactions": 1.3,
    "metals and materials international": 4.0,
    "journal of materials research": 2.4,
    "materials research express": 1.5,
    "physics of metals and metallography": 0.8,
    "acta metallurgica": 2.0,
    "acta metallurgica et materialia": 2.5,
    "scripta metallurgica": 2.5,
    "scripta metallurgica et materialia": 3.0,
    "nanostructured materials": 1.5,
    "international journal of materials research": 1.2,
}


def norm(name: str) -> str:
    if not name:
        return ""
    s = name.lower().strip()
    s = s.replace("&", "and")
    for ch in ".,:()[]{}/":
        s = s.replace(ch, " ")
    while "  " in s:
        s = s.replace("  ", " ")
    return s.strip()


IF_MAP = {norm(k): v for k, v in JOURNAL_IF.items()}


def get_if(journal_name: str):
    """精确匹配，返回 (IF, 是否命中参考表)"""
    n = norm(journal_name)
    if not n:
        return 0.0, False
    if n in IF_MAP:
        return IF_MAP[n], True
    return 0.0, False
