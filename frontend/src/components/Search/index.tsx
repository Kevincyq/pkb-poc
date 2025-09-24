import { useState, useRef, useEffect } from 'react';
import { Input } from 'antd';
import { SearchOutlined, CloseOutlined } from '@ant-design/icons';

interface SearchProps {
  onSearch: (value: string) => void;
}

export default function Search({ onSearch }: SearchProps) {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const inputRef = useRef<any>(null);

  useEffect(() => {
    if (isSearchOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isSearchOpen]);

  const handleSearchClick = () => {
    setIsSearchOpen(true);
  };

  const handleCloseSearch = () => {
    setIsSearchOpen(false);
    setSearchValue('');
    onSearch('');
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
    onSearch(value);
  };

  if (!isSearchOpen) {
    return (
      <SearchOutlined 
        onClick={handleSearchClick}
        style={{ 
          fontSize: '16px', 
          cursor: 'pointer',
          color: '#666'
        }} 
      />
    );
  }

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      <Input
        ref={inputRef}
        value={searchValue}
        onChange={handleInputChange}
        placeholder="在合集中搜索"
        style={{
          width: '240px',
          height: '32px',
          background: '#f5f5f5',
          border: 'none',
          borderRadius: '4px',
          fontSize: '14px',
          paddingRight: '32px'
        }}
      />
      {searchValue ? (
        <CloseOutlined
          onClick={handleCloseSearch}
          style={{
            position: 'absolute',
            right: '8px',
            fontSize: '14px',
            color: '#999',
            cursor: 'pointer'
          }}
        />
      ) : null}
    </div>
  );
}
