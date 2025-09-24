-- 检查向量索引状态
select 
    c.title,
    c.modality,
    count(ch.id) as chunk_count,
    count(ch.id) filter (where ch.embedding is not null) as with_embedding,
    max(length(ch.text)) as max_text_length,
    case 
        when count(ch.id) filter (where ch.embedding is not null) > 0 then 'OK'
        else 'Missing'
    end as embedding_status
from contents c
left join chunks ch on c.id = ch.content_id
where c.modality = 'image'
group by c.id, c.title, c.modality
order by c.created_at desc;
