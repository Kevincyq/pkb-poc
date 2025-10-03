/**
 * DocumentCard 组件单元测试
 * 测试文档卡片显示、缩略图、分类标签等功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import DocumentCard from '../components/Document/DocumentCard'

// Mock API base URL
vi.mock('../services/api', () => ({
  default: {
    defaults: {
      baseURL: 'http://localhost:8003/api'
    }
  }
}))

describe('DocumentCard', () => {
  const mockDocument = {
    id: 'test-doc-id',
    title: '测试文档.pdf',
    text: '这是一个测试文档的内容',
    sourceUri: 'webui://测试文档.pdf',
    modality: 'text' as const,
    createdAt: '2024-10-03T10:30:00Z',
    categories: [
      {
        id: 'cat-1',
        name: '职场商务',
        confidence: 0.85,
        role: 'primary_system' as const,
        source: 'ml' as const,
        color: 'blue',
        is_system: true
      }
    ]
  }

  beforeEach(() => {
    // 清理所有mock
    vi.clearAllMocks()
  })

  it('应该正确渲染文档基本信息', () => {
    render(<DocumentCard document={mockDocument} />)
    
    expect(screen.getByText('测试文档.pdf')).toBeInTheDocument()
    expect(screen.getByText('这是一个测试文档的内容')).toBeInTheDocument()
  })

  it('应该显示文档类型图标', () => {
    render(<DocumentCard document={mockDocument} />)
    
    // 查找文档类型图标
    const typeIcon = screen.getByRole('img', { hidden: true })
    expect(typeIcon).toBeInTheDocument()
  })

  it('应该显示分类标签', () => {
    render(<DocumentCard document={mockDocument} />)
    
    expect(screen.getByText('职场商务')).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('应该为主分类显示星号图标', () => {
    render(<DocumentCard document={mockDocument} />)
    
    // 主分类应该有星号图标
    const primaryTag = screen.getByText('职场商务').closest('.ant-tag')
    expect(primaryTag).toHaveTextContent('⭐')
  })

  it('应该为次分类显示链接图标', () => {
    const docWithSecondary = {
      ...mockDocument,
      categories: [
        ...mockDocument.categories,
        {
          id: 'cat-2',
          name: '学习成长',
          confidence: 0.45,
          role: 'secondary_system' as const,
          source: 'ml' as const,
          color: 'cyan',
          is_system: true
        }
      ]
    }

    render(<DocumentCard document={docWithSecondary} />)
    
    const secondaryTag = screen.getByText('学习成长').closest('.ant-tag')
    expect(secondaryTag).toHaveTextContent('🔗')
  })

  it('应该为用户规则显示文件夹图标', () => {
    const docWithUserRule = {
      ...mockDocument,
      categories: [
        ...mockDocument.categories,
        {
          id: 'cat-3',
          name: '我的项目',
          confidence: 0.90,
          role: 'user_rule' as const,
          source: 'rule' as const,
          color: 'green',
          is_system: false
        }
      ]
    }

    render(<DocumentCard document={docWithUserRule} />)
    
    const userRuleTag = screen.getByText('我的项目').closest('.ant-tag')
    expect(userRuleTag).toHaveTextContent('📁')
  })

  it('应该正确生成图片缩略图URL', () => {
    const imageDoc = {
      ...mockDocument,
      title: '度假照片.jpg',
      sourceUri: 'webui://度假照片.jpg',
      modality: 'image' as const
    }

    render(<DocumentCard document={imageDoc} />)
    
    // 查找图片元素
    const img = screen.getByRole('img', { name: /度假照片/ })
    expect(img).toHaveAttribute('src', expect.stringContaining('/files/thumbnail/'))
    expect(img).toHaveAttribute('src', expect.stringContaining(encodeURIComponent('度假照片.jpg')))
  })

  it('应该处理缩略图加载失败', () => {
    const imageDoc = {
      ...mockDocument,
      title: '不存在的图片.jpg',
      sourceUri: 'webui://不存在的图片.jpg',
      modality: 'image' as const
    }

    render(<DocumentCard document={imageDoc} />)
    
    const img = screen.getByRole('img', { name: /不存在的图片/ })
    
    // 模拟图片加载失败
    img.dispatchEvent(new Event('error'))
    
    // 应该显示默认图标而不是图片
    expect(img).toHaveAttribute('src', expect.not.stringContaining('/files/thumbnail/'))
  })

  it('应该显示创建时间', () => {
    render(<DocumentCard document={mockDocument} />)
    
    // 查找时间显示
    expect(screen.getByText(/2024/)).toBeInTheDocument()
  })

  it('应该处理没有分类的文档', () => {
    const docWithoutCategories = {
      ...mockDocument,
      categories: []
    }

    render(<DocumentCard document={docWithoutCategories} />)
    
    // 应该不显示分类标签
    expect(screen.queryByText('职场商务')).not.toBeInTheDocument()
  })

  it('应该处理长文本内容的截断', () => {
    const docWithLongText = {
      ...mockDocument,
      text: '这是一个非常长的文档内容，'.repeat(50) // 创建很长的文本
    }

    render(<DocumentCard document={docWithLongText} />)
    
    // 文本应该被截断
    const textElement = screen.getByText(/这是一个非常长的文档内容/)
    expect(textElement.textContent?.length).toBeLessThan(docWithLongText.text.length)
  })

  it('应该正确处理不同的文件类型', () => {
    const fileTypes = [
      { modality: 'text', title: 'document.txt' },
      { modality: 'image', title: 'photo.jpg' },
      { modality: 'pdf', title: 'report.pdf' }
    ]

    fileTypes.forEach(({ modality, title }) => {
      const doc = {
        ...mockDocument,
        modality: modality as any,
        title,
        sourceUri: `webui://${title}`
      }

      const { unmount } = render(<DocumentCard document={doc} />)
      
      expect(screen.getByText(title)).toBeInTheDocument()
      
      unmount()
    })
  })

  it('应该处理特殊字符的文件名', () => {
    const specialCharsDoc = {
      ...mockDocument,
      title: '测试文档 (副本) [重要].pdf',
      sourceUri: 'webui://测试文档 (副本) [重要].pdf'
    }

    render(<DocumentCard document={specialCharsDoc} />)
    
    expect(screen.getByText('测试文档 (副本) [重要].pdf')).toBeInTheDocument()
  })

  it('应该正确显示置信度百分比', () => {
    const confidenceTestCases = [
      { confidence: 0.95, expected: '95%' },
      { confidence: 0.5, expected: '50%' },
      { confidence: 0.123, expected: '12%' }
    ]

    confidenceTestCases.forEach(({ confidence, expected }) => {
      const doc = {
        ...mockDocument,
        categories: [{
          ...mockDocument.categories[0],
          confidence
        }]
      }

      const { unmount } = render(<DocumentCard document={doc} />)
      
      expect(screen.getByText(expected)).toBeInTheDocument()
      
      unmount()
    })
  })
})
