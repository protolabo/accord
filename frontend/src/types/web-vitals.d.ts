declare module "web-vitals" {
  export type Metric = {
    id: string;
    name: string;
    value: number;
    delta?: number;
    entries: PerformanceEntry[];
  };

  export type ReportHandler = (metric: Metric) => void;

  export function onCLS(reportHandler: ReportHandler): void;
  export function onFID(reportHandler: ReportHandler): void;
  export function onFCP(reportHandler: ReportHandler): void;
  export function onLCP(reportHandler: ReportHandler): void;
  export function onTTFB(reportHandler: ReportHandler): void;
}
