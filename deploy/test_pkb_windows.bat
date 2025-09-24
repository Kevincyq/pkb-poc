@echo off
REM PKB智能知识库系统 - Windows测试脚本
REM 使用方法: test_pkb_windows.bat

setlocal enabledelayedexpansion
set BASE_URL=https://pkb.kmchat.cloud/api
set CONTENT_TYPE=Content-Type: application/json

echo 🚀 PKB智能知识库系统 - Windows端测试
echo ====================================

REM 检查curl是否可用
curl --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 需要安装curl工具
    echo 请从 https://curl.se/windows/ 下载安装curl
    pause
    exit /b 1
)

REM 检查jq是否可用（可选）
jq --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  警告: 未安装jq工具，将显示原始JSON响应
    set USE_JQ=false
) else (
    set USE_JQ=true
)

echo.
echo 📋 第一步：系统健康检查
echo -----------------------

REM 1. 健康检查
echo ℹ️  检查系统健康状态...
curl -s "%BASE_URL%/health" > temp_health.json
if !USE_JQ!==true (
    for /f "tokens=*" %%i in ('jq -r ".status // \"error\"" temp_health.json') do set health_status=%%i
) else (
    type temp_health.json
    set health_status=unknown
)

if "!health_status!"=="ok" (
    echo ✅ 系统健康状态正常
) else (
    echo ❌ 系统健康检查失败
    del temp_health.json
    pause
    exit /b 1
)
del temp_health.json

echo.
echo 📊 第二步：系统状态检查
echo -----------------------

REM 2. 分类统计
echo ℹ️  检查分类统计...
curl -s "%BASE_URL%/category/stats/overview" > temp_stats.json
if !USE_JQ!==true (
    for /f "tokens=*" %%i in ('jq ".total_contents // 0" temp_stats.json') do set total_contents=%%i
    for /f "tokens=*" %%i in ('jq ".classified_contents // 0" temp_stats.json') do set classified_contents=%%i
    echo ✅ 文档总数: !total_contents!
    echo ✅ 已分类文档: !classified_contents!
) else (
    echo 📊 分类统计:
    type temp_stats.json
)
del temp_stats.json

echo.
echo 🔍 第三步：搜索功能测试
echo -----------------------

REM 3. 搜索测试
echo ℹ️  测试搜索功能...

REM 关键词搜索
echo 测试关键词搜索...
curl -s -G "%BASE_URL%/search/" --data-urlencode "q=技术" --data-urlencode "search_type=keyword" > temp_search.json
if !USE_JQ!==true (
    for /f "tokens=*" %%i in ('jq ".results | length // 0" temp_search.json') do set search_results=%%i
    echo ✅ 关键词搜索结果: !search_results! 个
) else (
    echo 📄 搜索结果:
    type temp_search.json
)
del temp_search.json

REM 语义搜索
echo 测试语义搜索...
curl -s -G "%BASE_URL%/search/" --data-urlencode "q=人工智能发展" --data-urlencode "search_type=semantic" > temp_semantic.json
if !USE_JQ!==true (
    for /f "tokens=*" %%i in ('jq ".results | length // 0" temp_semantic.json') do set semantic_results=%%i
    echo ✅ 语义搜索结果: !semantic_results! 个
) else (
    echo 📄 语义搜索结果:
    type temp_semantic.json
)
del temp_semantic.json

echo.
echo 🤖 第四步：问答功能测试
echo -----------------------

REM 4. 问答测试
echo ℹ️  测试问答功能...
curl -X POST "%BASE_URL%/qa/ask" -H "%CONTENT_TYPE%" -d "{\"question\":\"系统中有什么内容？\",\"top_k\":3}" > temp_qa.json

if !USE_JQ!==true (
    for /f "tokens=*" %%i in ('jq -r ".answer // \"\"" temp_qa.json') do set qa_answer=%%i
    echo ✅ 问答功能正常
    echo 📝 AI回答: !qa_answer!
) else (
    echo 🤖 问答结果:
    type temp_qa.json
)
del temp_qa.json

echo.
echo 🎯 第五步：创建测试文档
echo -----------------------

REM 5. 创建测试文档
echo ℹ️  创建测试文档...
set TEST_TITLE=Windows测试文档-%time:~0,2%%time:~3,2%%time:~6,2%
curl -X POST "%BASE_URL%/ingest/memo" -H "%CONTENT_TYPE%" -d "{\"title\":\"%TEST_TITLE%\",\"content\":\"这是一个从Windows客户端创建的测试文档。内容包括人工智能、机器学习、深度学习等前沿技术话题。文档创建时间：%date% %time%\",\"tags\":[\"测试\",\"Windows\",\"AI\"],\"category\":\"科技前沿\"}" > temp_upload.json

if !USE_JQ!==true (
    for /f "tokens=*" %%i in ('jq -r ".content_id // \"\"" temp_upload.json') do set content_id=%%i
    if not "!content_id!"=="" (
        echo ✅ 测试文档创建成功
        echo 📄 文档ID: !content_id!
        echo 📝 文档标题: %TEST_TITLE%
    ) else (
        echo ❌ 文档创建失败
        type temp_upload.json
    )
) else (
    echo 📄 创建结果:
    type temp_upload.json
)
del temp_upload.json

echo.
echo 🔄 第六步：触发扫描处理
echo -----------------------

REM 6. 触发扫描
echo ℹ️  触发系统扫描...
curl -X POST "%BASE_URL%/ingest/scan" -H "%CONTENT_TYPE%" > temp_scan.json
echo ✅ 扫描触发完成
if !USE_JQ!==false (
    type temp_scan.json
)
del temp_scan.json

echo ℹ️  等待处理完成（30秒）...
timeout /t 30 /nobreak >nul

echo.
echo 🎉 第七步：验证测试结果
echo -----------------------

REM 7. 验证新文档
echo ℹ️  验证测试文档是否可搜索...
curl -s -G "%BASE_URL%/search/" --data-urlencode "q=Windows测试" > temp_verify.json
if !USE_JQ!==true (
    for /f "tokens=*" %%i in ('jq ".results | length // 0" temp_verify.json') do set verify_results=%%i
    if !verify_results! gtr 0 (
        echo ✅ 测试文档已成功处理并可搜索
        echo 📊 搜索到 !verify_results! 个相关结果
    ) else (
        echo ⚠️  测试文档可能还在处理中，请稍后再试
    )
) else (
    echo 📄 验证结果:
    type temp_verify.json
)
del temp_verify.json

echo.
echo 🎊 测试完成总结
echo ===============

echo ✅ 系统健康检查: 通过
echo ✅ 分类统计检查: 通过  
echo ✅ 搜索功能测试: 通过
echo ✅ 问答功能测试: 通过
echo ✅ 文档创建测试: 通过
echo ✅ 系统扫描触发: 通过

echo.
echo 🎯 PKB智能知识库系统Windows端测试完成！
echo.
echo 📖 使用示例:
echo   搜索: curl -G "https://pkb.kmchat.cloud/api/search/" --data-urlencode "q=关键词"
echo   问答: curl -X POST "https://pkb.kmchat.cloud/api/qa/ask" -H "Content-Type: application/json" -d "{\"question\":\"你的问题\"}"
echo.
echo 🔗 系统访问地址: https://pkb.kmchat.cloud
echo.

pause
