#!/usr/bin/env python3
"""
编码问题诊断脚本
检查数据库中文档的编码问题
"""

import os
import sys
sys.path.append('/app')

from app.db import SessionLocal
from app.models import Content, Chunk
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_encoding_issues():
    """诊断编码问题"""
    db = SessionLocal()
    try:
        # 检查文档内容
        logger.info("=== 检查文档编码问题 ===")
        
        docs = db.query(Content).limit(5).all()
        for doc in docs:
            logger.info(f"\n文档: {doc.title}")
            logger.info(f"来源: {doc.source_uri}")
            logger.info(f"创建者: {doc.created_by}")
            
            # 检查文本内容
            text_sample = doc.text[:200] if doc.text else ""
            logger.info(f"文本样例 (前200字符):")
            logger.info(repr(text_sample))
            
            # 检查是否有乱码特征
            has_issues = False
            if '?' in text_sample or '�' in text_sample:
                logger.warning("  ⚠️  发现可能的编码问题: 包含 ? 或 � 字符")
                has_issues = True
            
            # 检查是否有异常字符
            try:
                text_sample.encode('utf-8')
                logger.info("  ✅ UTF-8 编码检查通过")
            except UnicodeEncodeError as e:
                logger.error(f"  ❌ UTF-8 编码检查失败: {e}")
                has_issues = True
            
            if not has_issues:
                logger.info("  ✅ 编码正常")
        
        # 检查文本块
        logger.info("\n=== 检查文本块编码问题 ===")
        
        chunks = db.query(Chunk).join(Content).limit(10).all()
        encoding_issues = 0
        
        for chunk in chunks:
            text_sample = chunk.text[:100] if chunk.text else ""
            
            # 检查乱码字符
            if '?' in text_sample or '�' in text_sample or '\ufffd' in text_sample:
                encoding_issues += 1
                logger.warning(f"块 {chunk.id} 有编码问题:")
                logger.warning(f"  文档: {chunk.content.title if chunk.content else 'Unknown'}")
                logger.warning(f"  文本: {repr(text_sample)}")
        
        logger.info(f"\n总计检查 {len(chunks)} 个文本块，发现 {encoding_issues} 个编码问题")
        
        # 统计问题文档
        if encoding_issues > 0:
            logger.info("\n=== 编码问题统计 ===")
            
            # 按来源统计
            problem_sources = db.query(Content.source_uri).filter(
                Content.text.contains('?') | 
                Content.text.contains('�') | 
                Content.text.contains('\ufffd')
            ).distinct().all()
            
            logger.info(f"有编码问题的文档来源:")
            for source in problem_sources:
                logger.info(f"  - {source[0]}")
        
        return {
            "total_documents": len(docs),
            "total_chunks": len(chunks),
            "encoding_issues": encoding_issues,
            "problem_sources": len(problem_sources) if encoding_issues > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"诊断过程中出错: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("开始诊断编码问题...")
    result = diagnose_encoding_issues()
    print(f"\n诊断结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
