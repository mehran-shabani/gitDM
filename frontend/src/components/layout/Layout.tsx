import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  FileText,
  Users,
  Calendar,
  FlaskConical,
  Pill,
  BookOpen,
  Home,
  Menu,
  X,
  LogOut,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../hooks/useToast';

interface LayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'AI Summaries', href: '/ai-summaries', icon: FileText },
  { name: 'Patients', href: '/patients', icon: Users },
  { name: 'Encounters', href: '/encounters', icon: Calendar },
  { name: 'Lab Results', href: '/lab-results', icon: FlaskConical },
  { name: 'Medications', href: '/medications', icon: Pill },
  { name: 'Clinical References', href: '/clinical-references', icon: BookOpen },
];

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { addToast } = useToast();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    addToast('info', 'Logged Out', 'You have been successfully logged out.');
    navigate('/login');
  };

  // Global Escape key handler for closing sidebar
  useEffect(() => {
    if (!sidebarOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [sidebarOpen]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      <div
        role="button"
        aria-label="Close sidebar"
        tabIndex={0}
        className={cn(
          'fixed inset-0 z-50 bg-gray-900/80 lg:hidden',
          sidebarOpen ? 'block' : 'hidden'
        )}
        onClick={() => setSidebarOpen(false)}
        onKeyDown={(e) => {
          if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') {
            setSidebarOpen(false);
          }
        }}
      />
      
      {/* Sidebar */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="app-sidebar-title"
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-xl transition-transform duration-300 lg:translate-x-0 lg:static lg:inset-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-6 lg:justify-center">
          <h1 id="app-sidebar-title" className="text-xl font-bold text-gray-900">GITDM Client</h1>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        
        <nav className="mt-8 px-4">
          <ul className="space-y-1">
            {navigation.map((item) => {
              const isActive =
                location.pathname === item.href ||
                location.pathname.startsWith(item.href + '/');
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    aria-current={isActive ? 'page' : undefined}
                    className={cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-gray-100 text-gray-900'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    )}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        
        {/* Logout button at bottom of sidebar */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t">
          <Button
            variant="ghost"
            className="w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut className="h-5 w-5 mr-3" />
            Logout
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-72">
        <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-white px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900">
              {navigation.find(
                (item) =>
                  item.href === location.pathname || location.pathname.startsWith(item.href + '/')
              )?.name || 'Dashboard'}
            </h2>
          </div>
        </header>
        
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}