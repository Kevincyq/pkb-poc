import { Layout } from 'antd';
import { type ReactNode } from 'react';
import styles from './MainLayout.module.css';

const { Content } = Layout;

interface MainLayoutProps {
  children: ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <Layout className={styles.layout}>
      <Content className={styles.content}>
        {children}
      </Content>
    </Layout>
  );
}