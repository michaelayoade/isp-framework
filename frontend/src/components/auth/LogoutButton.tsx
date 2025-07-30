'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';
import { useAppAuth } from '@/contexts/auth-context';

interface LogoutButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg';
  showText?: boolean;
}

export function LogoutButton({ 
  variant = 'ghost', 
  size = 'default',
  showText = true 
}: LogoutButtonProps) {
  const router = useRouter();
  const { logout } = useAppAuth();
  
  const handleLogout = () => {
    logout();
    router.push('/login');
  };
  
  return (
    <Button 
      onClick={handleLogout}
      variant={variant}
      size={size}
      className="flex items-center gap-2"
    >
      <LogOut className="h-4 w-4" />
      {showText && 'Logout'}
    </Button>
  );
}
