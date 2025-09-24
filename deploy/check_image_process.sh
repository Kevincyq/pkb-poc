#!/bin/bash

echo "=== [1] 检查所有图片状态 ==="
docker exec -i deploy-postgres-1 psql -U pkb -d pkb -c "
select 
    id, 
    title, 
    meta->>'processing_status' as status,
    created_at,
    updated_at
from contents 
where modality='image' 
order by created_at desc;"

echo -e "\n=== [2] 检查图片的文本和分类 ==="
docker exec -i deploy-postgres-1 psql -U pkb -d pkb -c "
select 
    c.id,
    c.title,
    c.meta->>'processing_status' as status,
    left(ch.text, 100) as text_preview,
    cat.name as category,
    cc.confidence
from contents c
left join chunks ch on c.id = ch.content_id
left join content_categories cc on c.id = cc.content_id
left join categories cat on cc.category_id = cat.id
where c.modality = 'image'
order by c.created_at desc;"

echo -e "\n=== [3] 检查处理统计 ==="
docker exec -i deploy-postgres-1 psql -U pkb -d pkb -c "
select 
    count(*) as total_images,
    count(*) filter (where meta->>'processing_status' = 'completed') as completed,
    count(*) filter (where meta->>'processing_status' = 'pending') as pending,
    count(*) filter (where exists(select 1 from chunks where content_id = contents.id)) as with_text,
    count(*) filter (where exists(select 1 from content_categories where content_id = contents.id)) as with_category
from contents 
where modality = 'image';"

echo -e "\n=== [4] 检查worker处理日志 ==="
docker-compose logs pkb-worker-heavy --tail=100 | grep -E "process_image_content|Processing image|Successfully processed|Failed|error|Error"