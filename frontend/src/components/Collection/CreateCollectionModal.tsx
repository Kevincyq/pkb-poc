import { Modal, Form, Input, Switch, message } from 'antd';
import { useState } from 'react';
import api from '../../services/api';

interface CreateCollectionModalProps {
  open: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

interface CollectionFormData {
  name: string;
  description?: string;
  auto_match: boolean;
}

export default function CreateCollectionModal({ 
  open, 
  onCancel, 
  onSuccess 
}: CreateCollectionModalProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: CollectionFormData) => {
    setLoading(true);
    try {
      console.log('🚀 Creating collection with data:', values);
      
      const response = await api.post('/collection/', values);
      console.log('✅ Collection created successfully:', response.data);
      
      message.success(`合集 "${values.name}" 创建成功！${values.auto_match ? '已自动匹配相关文档。' : ''}`);
      
      form.resetFields();
      onSuccess();
      
    } catch (error: any) {
      console.error('❌ Failed to create collection:', error);
      
      let errorMessage = '创建合集失败';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.status === 400) {
        errorMessage = '合集名称已存在或数据格式错误';
      }
      
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="创建智能合集"
      open={open}
      onCancel={handleCancel}
      onOk={() => form.submit()}
      confirmLoading={loading}
      okText="创建合集"
      cancelText="取消"
      width={500}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          auto_match: true
        }}
      >
        <Form.Item
          name="name"
          label="合集名称"
          rules={[
            { required: true, message: '请输入合集名称' },
            { min: 2, message: '合集名称至少2个字符' },
            { max: 50, message: '合集名称不能超过50个字符' }
          ]}
        >
          <Input 
            placeholder="例如：会议纪要、项目文档、学习笔记等"
            showCount
            maxLength={50}
          />
        </Form.Item>

        <Form.Item
          name="description"
          label="合集描述"
          rules={[
            { max: 200, message: '描述不能超过200个字符' }
          ]}
        >
          <Input.TextArea 
            placeholder="描述这个合集的用途和包含的内容类型（可选）"
            rows={3}
            showCount
            maxLength={200}
          />
        </Form.Item>

        <Form.Item
          name="auto_match"
          label="智能匹配"
          valuePropName="checked"
        >
          <Switch 
            checkedChildren="开启" 
            unCheckedChildren="关闭"
          />
        </Form.Item>
        
        <div style={{ 
          background: '#f6f8fa', 
          padding: '12px', 
          borderRadius: '6px',
          fontSize: '12px',
          color: '#666',
          marginTop: '8px'
        }}>
          <p style={{ margin: 0, marginBottom: '4px' }}>
            <strong>💡 智能匹配说明：</strong>
          </p>
          <p style={{ margin: 0 }}>
            开启后，系统会根据合集名称和描述自动匹配相关文档，并在上传新文档时自动归类到合适的合集中。
          </p>
        </div>
      </Form>
    </Modal>
  );
}
