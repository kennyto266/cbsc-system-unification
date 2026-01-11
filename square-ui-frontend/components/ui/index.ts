// Square UI Components
// 基於 Shadcn/ui 增強的 Square 風格組件庫

// Base UI Components (from Shadcn/ui)
export { Button } from './button';
export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';
export { Input } from './input';
export { Label } from './label';
export { Badge } from './badge';
export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
export { Avatar, AvatarFallback, AvatarImage } from './avatar';
export { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from './dropdown-menu';
export { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './table';

// Square Enhanced Components
export { SquareButton } from './square-button';
export type { SquareButtonProps } from './square-button';

export { SquareCard } from './square-card';
export type { SquareCardProps } from './square-card';

export { SquareBadge } from './square-badge';
export type { SquareBadgeProps } from './square-badge';

export { SquareInput } from './square-input';
export type { SquareInputProps } from './square-input';

// Re-export theme utilities
export { squareTheme, getSquareColor, getStatusColors } from '@/lib/square-theme';
export type { SquareTheme } from '@/lib/square-theme';