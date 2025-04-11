// Export as a named export for TypeScript compatibility
export interface MockEmail {
  "Message-ID": string;
  Subject: string;
  From: string;
  To: string;
  Cc: string;
  Date: string;
  "Content-Type": string;
  Body: string;
  IsRead: boolean;
  Attachments: {
    filename: string;
    contentType: string;
    size: number;
    contentId?: string;
    url?: string;
  }[];
  Categories: string[];
  Importance: "high" | "normal" | "low";
  ThreadId: string;
}

export const mockEmails: MockEmail[] = [
  {
    "Message-ID": "msg1",
    Subject: "Project Update",
    From: "john@example.com",
    To: "you@example.com",
    Cc: "team@example.com",
    Date: "2023-05-10T10:00:00Z",
    "Content-Type": "text/html",
    Body: "<p>Here's an update on our project progress.</p>",
    IsRead: false,
    Attachments: [
      {
        filename: "report.pdf",
        contentType: "application/pdf",
        size: 1024000,
        contentId: "att1",
      },
    ],
    Categories: ["Work", "Important"],
    Importance: "high",
    ThreadId: "thread1",
  },
  {
    "Message-ID": "msg2",
    Subject: "Weekend Plans",
    From: "friend@example.com",
    To: "you@example.com",
    Cc: "",
    Date: "2023-05-09T14:30:00Z",
    "Content-Type": "text/plain",
    Body: "Are you free this weekend? Let's catch up!",
    IsRead: true,
    Attachments: [],
    Categories: ["Personal"],
    Importance: "normal",
    ThreadId: "thread2",
  },
  {
    "Message-ID": "msg3",
    Subject: "Reminder: Meeting Tomorrow",
    From: "manager@example.com",
    To: "you@example.com, team@example.com",
    Cc: "",
    Date: "2023-05-08T09:15:00Z",
    "Content-Type": "text/html",
    Body: "<p>Don't forget our team meeting tomorrow at 10 AM.</p>",
    IsRead: false,
    Attachments: [
      {
        filename: "agenda.docx",
        contentType:
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size: 45000,
        contentId: "att2",
      },
    ],
    Categories: ["Work", "Meetings"],
    Importance: "high",
    ThreadId: "thread3",
  },
  {
    "Message-ID": "msg4",
    Subject: "Invoice #12345",
    From: "billing@example.com",
    To: "you@example.com",
    Cc: "",
    Date: "2023-05-07T16:45:00Z",
    "Content-Type": "text/html",
    Body: "<p>Your invoice is attached. Please pay within 30 days.</p>",
    IsRead: true,
    Attachments: [
      {
        filename: "invoice.pdf",
        contentType: "application/pdf",
        size: 320000,
        contentId: "att3",
      },
    ],
    Categories: ["Finance"],
    Importance: "normal",
    ThreadId: "thread4",
  },
  {
    "Message-ID": "msg5",
    Subject: "Newsletter: May 2023",
    From: "newsletter@example.com",
    To: "subscribers@example.com",
    Cc: "",
    Date: "2023-05-06T08:00:00Z",
    "Content-Type": "text/html",
    Body: "<h1>May Newsletter</h1><p>Here are this month's updates...</p>",
    IsRead: false,
    Attachments: [],
    Categories: ["Newsletter"],
    Importance: "low",
    ThreadId: "thread5",
  },
];

// Also add CommonJS exports for compatibility
module.exports = { mockEmails };
