

export interface Email {
  "Message-ID": string;
  Date: string;
  From: string;
  To: string;
  Subject: string;
  Body: string;
  Categories: string[];
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

export interface ThreadDetailProps {
  thread?: {
    subject: string;
  };
  emails: Email[];
}

export interface Attachment {
  name: string;
  type: string;
  size: number;
}