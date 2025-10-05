"""
常量定义 - 用于保持整个系统的一致性
"""

# 分类角色类型
class ClassificationRole:
    PRIMARY_SYSTEM = "primary_system"    # 主要系统分类（互斥）
    SECONDARY_TAG = "secondary_tag"      # 次要标签（多标签）
    USER_RULE = "user_rule"              # 用户规则分类

# 分类来源类型
class ClassificationSource:
    ML = "ml"                           # 机器学习/AI分类
    RULE = "rule"                       # 基于规则的分类
    HEURISTIC = "heuristic"             # 启发式/快速分类
    MANUAL = "manual"                   # 手动分类

# 标签类型
class TagType:
    AUTO = "auto"                       # 自动提取的标签
    MANUAL = "manual"                   # 手动添加的标签
    SYSTEM = "system"                   # 系统预置标签

# 信号类型
class SignalType:
    CLASSIFICATION = "classification"    # 分类决策信号
    TAG_EXTRACTION = "tag_extraction"   # 标签提取信号
    SEARCH = "search"                   # 搜索行为信号
    RECOMMENDATION = "recommendation"   # 推荐信号

# 搜索模式
class SearchMode:
    KEYWORD = "keyword"                 # 关键词搜索
    SEMANTIC = "semantic"               # 语义搜索
    HYBRID = "hybrid"                   # 混合搜索

# 分类阈值配置
class ClassificationThresholds:
    PRIMARY_HIGH = 0.70                 # 主分类高置信度阈值
    PRIMARY_DELTA = 0.08                # 主分类胶着判断差值
    SECONDARY_TAG = 0.55                # 次标签置信度阈值
    COLLECTION_SIMILARITY = 0.82        # 合集语义相似度阈值

# 融合搜索权重配置
class SearchWeights:
    BM25_WEIGHT = 0.30                  # 关键词搜索权重
    SEMANTIC_WEIGHT = 0.50              # 语义搜索权重
    TAG_BOOST_WEIGHT = 0.20             # 标签加权权重
