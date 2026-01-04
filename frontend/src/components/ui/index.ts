/**
 * UI Components Index - 統一導出所有UI組件
 * 版本: 1.0.0
 * 描述: 提供統一的UI組件導出入口
 */

// 基礎組件
export { default as Button, ButtonGroup, Fab } from './Button';
export type { ButtonProps, ButtonVariant, ButtonSize, ButtonGroupProps, FabProps } from './Button';

export { default as Input } from './Input';
export type { InputProps, InputVariant, InputSize, InputState } from './Input';

export { default as Select } from './Select';
export type { SelectProps, SelectVariant, SelectSize, SelectOption, SelectOptionGroup } from './Select';

// 布局組件
export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card';

// 狀單組件
export { Badge } from './Badge';
export { Pagination } from './Pagination';

// 輸入組件
export { default as Textarea } from './Textarea';
export { default as Progress } from './Progress';

// Table components
export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
} from './table';

// Dialog components
export {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './dialog';

// Dropdown menu components
export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from './dropdown-menu';

// Label component
export { Label } from './label';

// Tabs components
export { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs';

// Alert Dialog components
export {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogTrigger,
} from './alert-dialog';

// 工具函數
export { cn } from '../../utils/cn';
export { cva, type VariantProps } from '../../utils/class-variance-authority';
export { cnConditional, cnMultiConditional } from '../../utils/class-variance-authority';

// 設計令牌
import '../../styles/design-tokens.css';
