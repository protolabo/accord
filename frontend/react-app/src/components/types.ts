

export interface Email {
  "Message-ID": string;
  Date: string;
  From: string;
  To: string;
  Subject: string;
  Body: string | {
    plain?: string;
    html?: string;
  };
  Categories: string[];
  accord_sub_classes?: Array<[string, number]>;
  Cc?: string;
  IsRead?: boolean;
  Attachments?: {
    filename: string;
    contentType: string;
    size: number;
    contentId?: string;
    url?: string;
  }[];
  Importance?: "high" | "normal" | "low";
  ThreadId?: string;
}
export interface Notification {
  id: string;
  text: string;
}

export interface PriorityLevels {
  [key: string]: number;
}
export interface ThreadDetailProps {
  thread: Email | null;
  onBack: () => void;
}

export interface ThreadCategoryProps {
  category: string;
  emails: Email[];
  expanded: boolean;
  onToggle: () => void;
  index: number;
  totalCategories: number;
}

export interface ThreadSectionProps {
  groupedEmails: {
    [key: string]: Email[];
  };
}



export interface Attachment {
  name: string;
  type: string;
  size: number;
}