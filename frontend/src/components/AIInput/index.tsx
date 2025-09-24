import { Input, Button } from 'antd';

interface AIInputProps {
  onSend: (value: string) => void;
}

export default function AIInput({ onSend }: AIInputProps) {
  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      left: '50%',
      transform: 'translateX(-50%)',
      width: '90%',
      maxWidth: '800px',
      background: 'white',
      padding: '16px',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
    }}>
      <Input
        placeholder="我可以基于知识库收藏内容，为您搜索、总结、答疑解惑。"
        onPressEnter={(e) => onSend((e.target as HTMLInputElement).value)}
        suffix={
          <Button 
            type="text"
            onClick={() => {
              const input = document.querySelector('input') as HTMLInputElement;
              if (input?.value) {
                onSend(input.value);
                input.value = '';
              }
            }}
            style={{
              border: 'none',
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <svg 
              viewBox="0 0 24 24" 
              width="16" 
              height="16" 
              stroke="currentColor" 
              strokeWidth="2" 
              fill="none" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              style={{ color: '#1677ff' }}
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </Button>
        }
        style={{
          border: 'none',
          background: '#f5f5f5',
          borderRadius: '8px',
          padding: '8px 12px'
        }}
      />
    </div>
  );
}
