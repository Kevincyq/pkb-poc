import { ConfigProvider } from 'antd';
import { Outlet } from 'react-router-dom';
import zhCN from 'antd/locale/zh_CN';
import './App.css';

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#1677ff',
        },
      }}
    >
      <div style={{
        minHeight: '100vh',
        backgroundColor: '#fff',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <Outlet />
      </div>
    </ConfigProvider>
  );
}

export default App;