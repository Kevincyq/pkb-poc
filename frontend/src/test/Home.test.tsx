/**
 * Home 页面组件单元测试
 * 测试文件上传、搜索功能、状态轮询等核心功能
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Home from '../pages/Home'
import api from '../services/api'

// Mock API
vi.mock('../services/api')
const mockApi = vi.mocked(api)

// Mock antd message
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd')
  return {
    ...actual,
    message: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn(),
    }
  }
})

describe('Home Page', () => {
  const user = userEvent.setup()

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock successful API responses
    mockApi.get.mockResolvedValue({
      data: {
        results: [],
        total: 0,
        response_time: 0.1,
        search_type: 'hybrid',
        embedding_enabled: true
      }
    })

    mockApi.post.mockResolvedValue({
      data: {
        content_id: 'test-content-id',
        message: '文件上传成功',
        filename: 'test.txt'
      }
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('应该正确渲染主页面', () => {
    render(<Home />)
    
    expect(screen.getByText('个人知识库')).toBeInTheDocument()
    expect(screen.getByText('拖拽文件到此处或点击上传')).toBeInTheDocument()
  })

  it('应该显示搜索按钮', () => {
    render(<Home />)
    
    const searchButton = screen.getByRole('button', { name: /search/i })
    expect(searchButton).toBeInTheDocument()
  })

  it('应该能够打开搜索模态框', async () => {
    render(<Home />)
    
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    expect(screen.getByText('高级搜索')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('输入搜索关键词')).toBeInTheDocument()
  })

  it('应该能够执行搜索', async () => {
    mockApi.get.mockResolvedValueOnce({
      data: {
        results: [
          {
            content_id: 'result-1',
            title: '搜索结果1',
            text: '这是搜索到的内容',
            score: 0.85,
            source_uri: 'webui://result1.txt'
          }
        ],
        total: 1,
        response_time: 0.2,
        search_type: 'hybrid',
        embedding_enabled: true
      }
    })

    render(<Home />)
    
    // 打开搜索模态框
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    // 输入搜索关键词
    const searchInput = screen.getByPlaceholderText('输入搜索关键词')
    await user.type(searchInput, '测试搜索')
    
    // 点击搜索按钮
    const performSearchButton = screen.getByRole('button', { name: '搜索' })
    await user.click(performSearchButton)
    
    // 验证API调用
    await waitFor(() => {
      expect(mockApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/search?q=测试搜索')
      )
    })
  })

  it('应该处理空搜索查询', async () => {
    const { message } = await import('antd')
    
    render(<Home />)
    
    // 打开搜索模态框
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    // 不输入任何内容直接搜索
    const performSearchButton = screen.getByRole('button', { name: '搜索' })
    await user.click(performSearchButton)
    
    // 应该显示警告消息
    expect(message.warning).toHaveBeenCalledWith('请输入搜索关键词')
  })

  it('应该处理搜索查询过长', async () => {
    const { message } = await import('antd')
    
    render(<Home />)
    
    // 打开搜索模态框
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    // 输入过长的搜索查询
    const searchInput = screen.getByPlaceholderText('输入搜索关键词')
    const longQuery = 'a'.repeat(201)
    await user.type(searchInput, longQuery)
    
    const performSearchButton = screen.getByRole('button', { name: '搜索' })
    await user.click(performSearchButton)
    
    // 应该显示警告消息
    expect(message.warning).toHaveBeenCalledWith('搜索关键词过长，请缩短后重试')
  })

  it('应该能够设置搜索过滤条件', async () => {
    render(<Home />)
    
    // 打开搜索模态框
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    // 设置分类过滤
    const categorySelect = screen.getByText('选择分类')
    await user.click(categorySelect)
    
    // 这里可以添加更多的过滤条件测试
    expect(screen.getByText('职场商务')).toBeInTheDocument()
    expect(screen.getByText('生活点滴')).toBeInTheDocument()
  })

  it('应该能够重置搜索过滤条件', async () => {
    render(<Home />)
    
    // 打开搜索模态框
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    // 点击重置按钮
    const resetButton = screen.getByRole('button', { name: '重置' })
    await user.click(resetButton)
    
    // 验证过滤条件被重置
    const searchInput = screen.getByPlaceholderText('输入搜索关键词')
    expect(searchInput).toHaveValue('')
  })

  it('应该处理搜索API错误', async () => {
    const { message } = await import('antd')
    
    // 模拟API错误
    mockApi.get.mockRejectedValueOnce(new Error('网络错误'))
    
    render(<Home />)
    
    // 打开搜索模态框并执行搜索
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    const searchInput = screen.getByPlaceholderText('输入搜索关键词')
    await user.type(searchInput, '测试')
    
    const performSearchButton = screen.getByRole('button', { name: '搜索' })
    await user.click(performSearchButton)
    
    // 应该显示错误消息
    await waitFor(() => {
      expect(message.error).toHaveBeenCalledWith('搜索失败，请重试')
    })
  })

  it('应该处理不同类型的搜索错误', async () => {
    const { message } = await import('antd')
    
    const errorCases = [
      { status: 400, expectedMessage: '搜索参数有误，请检查输入' },
      { status: 500, expectedMessage: '服务器错误，请稍后重试' }
    ]

    for (const { status, expectedMessage } of errorCases) {
      // 清理之前的mock调用
      vi.clearAllMocks()
      
      // 模拟特定的HTTP错误
      mockApi.get.mockRejectedValueOnce({
        response: { status }
      })
      
      render(<Home />)
      
      const searchButton = screen.getByRole('button', { name: /search/i })
      await user.click(searchButton)
      
      const searchInput = screen.getByPlaceholderText('输入搜索关键词')
      await user.type(searchInput, '测试')
      
      const performSearchButton = screen.getByRole('button', { name: '搜索' })
      await user.click(performSearchButton)
      
      await waitFor(() => {
        expect(message.error).toHaveBeenCalledWith(expectedMessage)
      })
    }
  })

  it('应该显示搜索结果', async () => {
    const mockResults = [
      {
        content_id: 'result-1',
        title: '测试文档1.pdf',
        text: '这是第一个搜索结果',
        score: 0.9,
        source_uri: 'webui://测试文档1.pdf',
        modality: 'text',
        created_at: '2024-10-03T10:00:00Z',
        categories: []
      },
      {
        content_id: 'result-2',
        title: '测试图片.jpg',
        text: '这是第二个搜索结果',
        score: 0.8,
        source_uri: 'webui://测试图片.jpg',
        modality: 'image',
        created_at: '2024-10-03T11:00:00Z',
        categories: []
      }
    ]

    mockApi.get.mockResolvedValueOnce({
      data: {
        results: mockResults,
        total: 2,
        response_time: 0.3,
        search_type: 'hybrid',
        embedding_enabled: true
      }
    })

    render(<Home />)
    
    // 执行搜索
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    const searchInput = screen.getByPlaceholderText('输入搜索关键词')
    await user.type(searchInput, '测试')
    
    const performSearchButton = screen.getByRole('button', { name: '搜索' })
    await user.click(performSearchButton)
    
    // 验证搜索结果显示
    await waitFor(() => {
      expect(screen.getByText('测试文档1.pdf')).toBeInTheDocument()
      expect(screen.getByText('测试图片.jpg')).toBeInTheDocument()
    })
  })

  it('应该显示无搜索结果的提示', async () => {
    const { message } = await import('antd')
    
    mockApi.get.mockResolvedValueOnce({
      data: {
        results: [],
        total: 0,
        response_time: 0.1,
        search_type: 'hybrid',
        embedding_enabled: true
      }
    })

    render(<Home />)
    
    // 执行搜索
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    const searchInput = screen.getByPlaceholderText('输入搜索关键词')
    await user.type(searchInput, '不存在的内容')
    
    const performSearchButton = screen.getByRole('button', { name: '搜索' })
    await user.click(performSearchButton)
    
    // 应该显示无结果提示
    await waitFor(() => {
      expect(message.info).toHaveBeenCalledWith('没有找到相关内容，请尝试使用不同的关键词或调整过滤条件')
    })
  })

  it('应该能够关闭搜索模态框', async () => {
    render(<Home />)
    
    // 打开搜索模态框
    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)
    
    expect(screen.getByText('高级搜索')).toBeInTheDocument()
    
    // 点击取消按钮关闭
    const cancelButton = screen.getByRole('button', { name: '取消' })
    await user.click(cancelButton)
    
    // 模态框应该被关闭
    expect(screen.queryByText('高级搜索')).not.toBeInTheDocument()
  })
})
