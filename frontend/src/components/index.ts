// Export all components for easy importing

// Square-UI components
export { Button, ButtonGroup, Fab } from './ui/Button';
export { Input } from './ui/Input';
export { Select } from './ui/Select';
export { Card } from './ui/Card';
export { Badge } from './ui/Badge';
export { Modal as SquareModal } from './ui/Modal';
export { StatCard } from './ui/StatCard';
export { QuickActions } from './ui/QuickActions';
export { ThemeToggle } from './ui/ThemeToggle';
export { LoadingSpinner } from './ui/LoadingSpinner';
export { RecentActivities } from './ui/RecentActivities';

// UI Helper components (migrated from unified-dashboard)
export {
  Grid,
  GridItem,
  ResponsiveGrid,
  DashboardGrid,
  MetricsGrid,
  ChartGrid,
  FlexibleGrid,
} from './ui-helpers';
export { MetricCard } from './ui-helpers';

// Analytics components (migrated from unified-dashboard)
export { PerformanceMetrics, RiskMetrics } from './analytics';

// shadcn/ui components
export { ShadcnButton as Button } from './ui/shadcn-button';
export { ShadcnInput as Input } from './ui/shadcn-input';
export { ShadcnSelect as Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from './ui/shadcn-select';
export { ShadcnCard as Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from './ui/shadcn-card';
export { Label } from './ui/label';
export { Dialog, DialogPortal, DialogOverlay, DialogTrigger, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription, DialogClose } from './ui/dialog';
export { Table, TableHeader, TableBody, TableFooter, TableHead, TableRow, TableCell, TableCaption } from './ui/table';
export { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
export { Textarea } from './ui/textarea';
export { Checkbox } from './ui/checkbox';
export { RadioGroup, RadioGroupItem } from './ui/radio-group';
export { Switch } from './ui/switch';
export { Slider } from './ui/slider';
export { Progress } from './ui/progress';
export { Calendar } from './ui/calendar';
export { Popover, PopoverTrigger, PopoverContent } from './ui/popover';
export { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from './ui/accordion';
export { Avatar, AvatarImage, AvatarFallback } from './ui/avatar';
export { Skeleton } from './ui/skeleton';
export { Separator } from './ui/separator';
export { ShadcnBadge as Badge } from './ui/shadcn-badge';
export { Toggle, ToggleGroup, ToggleGroupItem } from './ui/toggle';

// Combined components (Square-UI + shadcn/ui)
export {
  FormField,
  FormSection,
  FormActions,
} from './combined/FormField';
export {
  DataTable,
  type ExtendedColumnDef,
} from './combined/DataTable';
export {
  Modal,
  ConfirmModal,
  InfoModal,
  FormModal,
  useModal,
} from './combined/Modal';
export {
  Alert,
  AlertBanner,
  InlineAlert,
  Toast,
  ToastAction,
  ToastContainer,
  ToastViewport,
  ToastProvider,
  useToast,
  toast,
} from './combined/Alert';

// Examples
export { ComponentExamples } from './combined/Examples';

// Re-export hooks
export { useIntersectionObserver } from '../hooks/useIntersectionObserver';
export { useResponsive } from '../hooks/useResponsive';
export { useWebSocketEnhanced } from '../hooks/useWebSocketEnhanced';
export { useCSRF } from '../hooks/useCSRF';
export { useXSS } from '../hooks/useXSS';

// Utilities
export { cn } from '../lib/utils';
export { validationUtils } from '../lib/validations';
export * from '../lib/validations';