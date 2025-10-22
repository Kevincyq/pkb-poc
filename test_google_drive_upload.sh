#!/bin/bash

# Google Drive文件上传测试脚本

if [ $# -lt 1 ]; then
    echo "使用方法:"
    echo "  $0 <JWT_TOKEN>                    # 测试默认文件"
    echo "  $0 <JWT_TOKEN> <file_path>         # 上传指定文件"
    echo ""
    echo "示例:"
    echo "  $0 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'"
    echo "  $0 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' /path/to/your/file.pdf"
    exit 1
fi

JWT_TOKEN=$1
BASE_URL="http://34.247.12.46:8010"
CUSTOM_FILE=""

# 检查是否有自定义文件参数
if [ $# -eq 2 ]; then
    CUSTOM_FILE="$2"
    if [ ! -f "$CUSTOM_FILE" ]; then
        echo "❌ 错误：文件 '$CUSTOM_FILE' 不存在！"
        exit 1
    fi
    echo "📁 将上传自定义文件: $CUSTOM_FILE"
    echo "文件大小: $(ls -lh "$CUSTOM_FILE" | awk '{print $5}')"
    echo ""
fi

echo "🔍 测试Google Drive文件上传功能..."
echo "JWT Token: ${JWT_TOKEN:0:50}..."
echo ""

# 创建测试文件（如果没有自定义文件）
if [ -z "$CUSTOM_FILE" ]; then
    echo "📝 创建测试文件..."
    echo "这是一个测试文件，用于验证Google Drive上传功能" > test_file.txt
    echo "Test content for Google Drive upload" > test_english.txt
    echo "Hello World! 你好世界！" > hello_world.txt
    echo "✅ 测试文件创建完成"
    echo ""
fi

# 上传文件函数
upload_file() {
    local file_path="$1"
    local file_name=$(basename "$file_path")
    local test_name="$2"
    
    echo "$test_name"
    echo "文件: $file_name"
    echo "路径: $file_path"
    
    UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/ingest/upload-smart" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -F "file=@$file_path")
    
    echo "上传响应:"
    echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"
    echo ""
    
    # 提取Content ID和文件ID
    CONTENT_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"content_id":"[^"]*"' | cut -d'"' -f4)
    FILE_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$CONTENT_ID" ]; then
        echo "✅ 文件上传成功，Content ID: $CONTENT_ID"
        
        # 提取存储策略和提供商
        STORAGE_STRATEGY=$(echo "$UPLOAD_RESPONSE" | grep -o '"storage_strategy":"[^"]*"' | cut -d'"' -f4)
        PROVIDER=$(echo "$UPLOAD_RESPONSE" | grep -o '"provider":"[^"]*"' | cut -d'"' -f4)
        echo "📦 存储策略: $STORAGE_STRATEGY"
        echo "☁️ 云盘提供商: $PROVIDER"
        
        # 测试下载（使用文件名而不是ID）
        echo "📥 测试文件下载..."
        DOWNLOAD_FILE="downloaded_${file_name}"
        curl -s -H "Authorization: Bearer $JWT_TOKEN" \
          "$BASE_URL/api/files/$file_name" \
          -o "$DOWNLOAD_FILE"
        
        if [ -f "$DOWNLOAD_FILE" ]; then
            echo "✅ 文件下载成功"
            echo "下载文件: $DOWNLOAD_FILE"
            
            # 如果是文本文件，显示内容
            if [[ "$file_name" == *.txt ]] || [[ "$file_name" == *.md ]] || [[ "$file_name" == *.log ]]; then
                echo "文件内容:"
                head -10 "$DOWNLOAD_FILE"
                if [ $(wc -l < "$DOWNLOAD_FILE") -gt 10 ]; then
                    echo "... (显示前10行)"
                fi
            fi
            
            # 测试缩略图（如果是图片文件）
            if [[ "$file_name" == *.jpg ]] || [[ "$file_name" == *.jpeg ]] || [[ "$file_name" == *.png ]] || [[ "$file_name" == *.gif ]]; then
                echo "🖼️ 测试缩略图生成..."
                curl -s -H "Authorization: Bearer $JWT_TOKEN" \
                  "$BASE_URL/api/files/thumbnail/$file_name" \
                  -o "thumbnail_${file_name}"
                
                if [ -f "thumbnail_${file_name}" ]; then
                    echo "✅ 缩略图生成成功"
                else
                    echo "❌ 缩略图生成失败"
                fi
            fi
        else
            echo "❌ 文件下载失败"
        fi
    else
        echo "❌ 文件上传失败"
    fi
    
    echo ""
    echo "----------------------------------------"
    echo ""
}

# 如果有自定义文件，只上传自定义文件
if [ ! -z "$CUSTOM_FILE" ]; then
    upload_file "$CUSTOM_FILE" "🎯 上传自定义文件"
else
    # 测试默认文件
    upload_file "test_file.txt" "1️⃣ 测试上传中文文件"
    upload_file "test_english.txt" "2️⃣ 测试上传英文文件"
    upload_file "hello_world.txt" "3️⃣ 测试上传混合语言文件"
fi

# 清理测试文件
if [ -z "$CUSTOM_FILE" ]; then
    echo "🧹 清理测试文件..."
    rm -f test_file.txt test_english.txt hello_world.txt downloaded_*.txt thumbnail_*
else
    echo "🧹 清理下载文件..."
    rm -f downloaded_* thumbnail_*
fi

echo "🎉 Google Drive文件上传测试完成！"
echo ""
echo "💡 提示："
echo "   - 检查Google Drive中的PKB-Files文件夹"
echo "   - 验证文件是否正确上传"
echo "   - 测试文件搜索功能"
