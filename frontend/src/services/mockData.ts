/**
 * Mock数据 - 用于本地开发和调试
 */

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock分类数据 - 5个系统默认分类
export const mockCategories = [
  { id: '1', name: 'Business', color: '#1890ff', content_count: 12 },
  { id: '2', name: 'Learning', color: '#52c41a', content_count: 2 },
  { id: '3', name: 'Life', color: '#faad14', content_count: 63 },
  { id: '4', name: 'Technology', color: '#722ed1', content_count: 32 },
  { id: '5', name: 'Art', color: '#ff7875', content_count: 8 },
];

// Mock文档数据
export const mockDocuments = [
  {
    content_id: 'doc1',
    chunk_id: 'chunk1',
    title: 'React最佳实践指南',
    modality: 'text' as const,
    source_uri: 'file://react-guide.pdf',
    created_at: '2024-01-15T10:30:00Z',
    category: '技术资料',
    category_name: '技术资料',
    category_color: '#f5222d',
    category_confidence: 0.95,
    score: 0.92,
    text: 'React是一个用于构建用户界面的JavaScript库...',
    tags: 'react,前端,最佳实践',
    match_type: 'semantic',
    chunk_type: 'paragraph',
  },
  {
    content_id: 'doc2',
    chunk_id: 'chunk2',
    title: '项目管理会议纪要',
    modality: 'text' as const,
    source_uri: 'file://meeting-notes.md',
    created_at: '2024-01-16T14:20:00Z',
    category: '工作文档',
    category_name: '工作文档',
    category_color: '#1890ff',
    category_confidence: 0.88,
    score: 0.85,
    text: '本次会议讨论了项目进度和下一步计划...',
    tags: '会议,项目管理',
    match_type: 'keyword',
    chunk_type: 'paragraph',
  },
  {
    content_id: 'doc3',
    chunk_id: 'chunk3',
    title: '机器学习入门笔记',
    modality: 'text' as const,
    source_uri: 'file://ml-notes.txt',
    created_at: '2024-01-17T09:15:00Z',
    category: '学习笔记',
    category_name: '学习笔记',
    category_color: '#52c41a',
    category_confidence: 0.91,
    score: 0.89,
    text: '机器学习是人工智能的一个分支...',
    tags: '机器学习,AI,学习',
    match_type: 'hybrid',
    chunk_type: 'paragraph',
  },
  {
    content_id: 'doc4',
    chunk_id: 'chunk4',
    title: '旅行照片',
    modality: 'image' as const,
    source_uri: 'file://travel-photo.jpg',
    created_at: '2024-01-18T16:45:00Z',
    category: '生活记录',
    category_name: '生活记录',
    category_color: '#faad14',
    category_confidence: 0.82,
    score: 0.78,
    text: '',
    tags: '旅行,照片',
    match_type: 'semantic',
    chunk_type: 'image',
  },
];

// Mock合集数据
export const mockCollections = [
  {
    id: 'coll1',
    name: '前端开发合集',
    description: '收集所有前端相关的文档和资料',
    content_count: 18,
    created_at: '2024-01-10T10:00:00Z',
    updated_at: '2024-01-20T15:30:00Z',
  },
  {
    id: 'coll2',
    name: 'AI学习资料',
    description: '人工智能和机器学习相关文档',
    content_count: 25,
    created_at: '2024-01-12T11:00:00Z',
    updated_at: '2024-01-19T10:20:00Z',
  },
];

// Mock问答历史
export const mockQAHistory: any[] = [
  {
    id: 'qa1',
    question: '什么是React？',
    answer: 'React是一个用于构建用户界面的JavaScript库，由Facebook开发。它采用组件化开发模式，使用虚拟DOM来提高性能。React的主要特点包括：组件化、声明式编程、单向数据流等。',
    session_id: 'session1',
    confidence: 0.95,
    created_at: '2024-01-20T10:00:00Z',
  },
  {
    id: 'qa2',
    question: '如何优化React性能？',
    answer: '优化React性能的方法包括：1. 使用React.memo避免不必要的重渲染 2. 使用useMemo和useCallback缓存计算结果 3. 代码分割和懒加载 4. 虚拟化长列表 5. 使用生产环境构建',
    session_id: 'session1',
    confidence: 0.92,
    created_at: '2024-01-20T10:05:00Z',
  },
  {
    id: 'qa3',
    question: 'React Hooks是什么？',
    answer: 'React Hooks是React 16.8引入的新特性，允许你在函数组件中使用状态和其他React特性。常用的Hooks包括useState、useEffect、useContext、useReducer等。Hooks让函数组件也能拥有类组件的功能。',
    session_id: 'session1',
    confidence: 0.90,
    created_at: '2024-01-20T10:10:00Z',
  },
  {
    id: 'qa4',
    question: 'Vue和React的区别是什么？',
    answer: 'Vue和React都是流行的前端框架，主要区别包括：1. Vue使用模板语法，React使用JSX 2. Vue的双向数据绑定 vs React的单向数据流 3. Vue的学习曲线相对平缓，React更灵活但需要更多配置 4. 生态系统和社区支持各有优势',
    session_id: 'session1',
    confidence: 0.88,
    created_at: '2024-01-20T10:15:00Z',
  },
  {
    id: 'qa5',
    question: '什么是虚拟DOM？',
    answer: '虚拟DOM是React的核心概念之一，它是一个JavaScript对象，用来描述真实DOM的结构。React通过比较新旧虚拟DOM的差异，只更新实际发生变化的部分，从而提高渲染性能。这种方式避免了直接操作DOM带来的性能开销。',
    session_id: 'session1',
    confidence: 0.93,
    created_at: '2024-01-20T10:20:00Z',
  },
];

// Mock问答响应
export const generateMockQAResponse = (question: string): any => {
  const answers: Record<string, string> = {
    '什么是React': 'React是一个用于构建用户界面的JavaScript库，由Facebook开发。它采用组件化开发模式，使用虚拟DOM来提高性能。React的主要特点包括：组件化、声明式编程、单向数据流等。',
    '如何优化React性能': '优化React性能的方法包括：1. 使用React.memo避免不必要的重渲染 2. 使用useMemo和useCallback缓存计算结果 3. 代码分割和懒加载 4. 虚拟化长列表 5. 使用生产环境构建',
    'React Hooks是什么': 'React Hooks是React 16.8引入的新特性，允许你在函数组件中使用状态和其他React特性。常用的Hooks包括useState、useEffect、useContext、useReducer等。',
  };

  const defaultAnswer = `关于"${question}"，根据知识库中的资料，我可以为您提供以下信息：这是一个很好的问题。让我从知识库中查找相关信息来回答您。`;

  return {
    question,
    answer: answers[question] || defaultAnswer,
    session_id: 'mock_session_' + Date.now(),
    confidence: 0.85 + Math.random() * 0.1,
    sources: mockDocuments.slice(0, 3).map((doc, index) => ({
      title: doc.title,
      text: doc.text || '相关文档内容',
      source_uri: doc.source_uri,
      score: 0.9 - index * 0.1,
      content_id: doc.content_id,
      category_name: doc.category_name,
      modality: doc.modality,
      confidence_percentage: Math.floor(85 + Math.random() * 10),
    })),
    qa_id: 'qa_' + Date.now(),
    tokens_used: 150 + Math.floor(Math.random() * 100),
    response_time: 0.5 + Math.random() * 0.5,
  };
};

// Mock上传响应
export const generateMockUploadResponse = (fileName: string, fileSize: number): any => {
  const contentId = 'content_' + Date.now();
  return {
    status: 'success',
    content_id: contentId,
    title: fileName,
    processing_status: 'uploaded',
    chunks_created: 0,
    file_size: fileSize,
    message: '文件上传成功，正在处理中...',
  };
};

// Mock处理状态
export const generateMockProcessingStatus = (contentId: string, fileName: string): any => {
  const statuses: Array<'uploaded' | 'parsing' | 'parsed' | 'processing' | 'completed' | 'error'> = 
    ['uploaded', 'parsing', 'parsed', 'processing', 'completed'];
  
  // 模拟处理进度
  const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
  
  return {
    content_id: contentId,
    title: fileName,
    processing_status: randomStatus,
    parsing_status: randomStatus === 'completed' ? 'completed' : 'parsing',
    classification_status: randomStatus === 'completed' ? 'completed' : 'quick_processing',
    show_classification: randomStatus === 'completed',
    file_type: fileName.split('.').pop() || 'txt',
    file_size: 1024 * 1024 * 2, // 2MB
    estimated_time: 5,
    categories: randomStatus === 'completed' ? [
      { id: '1', name: '技术资料', confidence: 0.92 },
      { id: '2', name: '工作文档', confidence: 0.75 },
    ] : [],
    created_at: new Date().toISOString(),
  };
};

// Mock推荐问题数据
export const mockRecommendedQuestions = [
  { id: 'rec1', question: 'Explain "Clause 4.2" in contract', content_id: 'doc1' },
  { id: 'rec2', question: 'Data extraction from PDF', content_id: 'doc2' },
  { id: 'rec3', question: 'Weekend Team Building', content_id: 'doc3' },
  { id: 'rec4', question: 'Ask about "Employee Handbook"', content_id: 'doc4' },
];

// Mock搜索响应
export const generateMockSearchResponse = (query: string, limit: number = 20): any => {
  // 根据查询关键词过滤文档
  const filteredDocs = mockDocuments.filter(doc => 
    doc.title.toLowerCase().includes(query.toLowerCase()) ||
    doc.text?.toLowerCase().includes(query.toLowerCase()) ||
    doc.tags?.toLowerCase().includes(query.toLowerCase())
  );

  return {
    results: filteredDocs.slice(0, limit),
    total: filteredDocs.length,
    query,
    search_type: 'hybrid',
  };
};


