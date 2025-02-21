import { Email, PriorityLevels , Notification } from '../components/types';

export const mockEmails: Email[] =[
    {
      "Message-ID": "<18782981.1075855378110.JavaMail.evans@thyme>",
      Date: "Mon, 14 May 2001 16:39:00 -0700",
      From: "phillip.allen@enron.com",
      To: "tim.belden@enron.com",
      Subject: "Here is our forecast",
      Body: "Here is our forecast for the upcoming quarter.",
      Categories: ["Other"],
    },
    {
      "Message-ID": "<15464986.1075855378456.JavaMail.evans@thyme>",
      Date: "Fri, 04 May 2001 13:51:00 -0700",
      From: "phillip.allen@enron.com",
      To: "john.lavorato@enron.com",
      Subject: "Re: Business trip",
      Body: "Traveling to have a business meeting takes the fun out of the trip...",
      Categories: ["Meeting Scheduling", "Business Discussion"],
    },
    {
      "Message-ID": "<24216240.1075855687451.JavaMail.evans@thyme>",
      Date: "Wed, 18 Oct 2000 03:00:00 -0700",
      From: "phillip.allen@enron.com",
      To: "leah.arsdall@enron.com",
      Subject: "Re: test",
      Body: "Test successful. Way to go!!!",
      Categories: ["System Testing & IT", "Information Distribution"],
    },
    {
      "Message-ID": "<13505866.1075863688222.JavaMail.evans@thyme>",
      Date: "Mon, 23 Oct 2000 06:13:00 -0700",
      From: "phillip.allen@enron.com",
      To: "randall.gay@enron.com",
      Subject: "Salary and schedule",
      Body: "Can you send me a schedule of the salary and level of everyone...",
      Categories: ["Meeting Scheduling", "Salary & Promotion"],
    },
    {
      "Message-ID": "<30922949.1075863688243.JavaMail.evans@thyme>",
      Date: "Thu, 31 Aug 2000 05:07:00 -0700",
      From: "phillip.allen@enron.com",
      To: "greg.piper@enron.com",
      Subject: "Re: Hello",
      Body: "Let's shoot for Tuesday at 11:45.",
      Categories: ["Scheduling Coordination"],
    },
    {
      "Message-ID": "<30965995.1075863688265.JavaMail.evans@thyme>",
      Date: "Thu, 31 Aug 2000 04:17:00 -0700",
      From: "phillip.allen@enron.com",
      To: "greg.piper@enron.com",
      Subject: "Re: Hello again",
      Body: "How about either next Tuesday or Thursday?",
      Categories: ["Scheduling Coordination"],
    },
    {
      "Message-ID": "<16254169.1075863688286.JavaMail.evans@thyme>",
      Date: "Tue, 22 Aug 2000 07:44:00 -0700",
      From: "phillip.allen@enron.com",
      To: "david.l.johnson@enron.com, john.shafer@enron.com",
      Subject: "Update distribution list",
      Body: "Please cc the following distribution list with updates...",
      Categories: ["System Updates", "Information Distribution"],
    },
    {
      "Message-ID": "<17189699.1075863688308.JavaMail.evans@thyme>",
      Date: "Fri, 14 Jul 2000 06:59:00 -0700",
      From: "phillip.allen@enron.com",
      To: "joyce.teixeira@enron.com",
      Subject: "Re: PRC review",
      Body: "Any morning between 10 and 11:30.",
      Categories: ["Other"],
    },
    {
      "Message-ID": "<18782982.1075855378111.JavaMail.evans@thyme>",
      Date: "Tue, 15 May 2001 10:39:00 -0700",
      From: "phillip.allen@enron.com",
      To: "tim.belden@enron.com",
      Subject: "Follow-up forecast",
      Body: "Here is an updated forecast.",
      Categories: ["Other"],
    },
    {
      "Message-ID": "<13505867.1075863688223.JavaMail.evans@thyme>",
      Date: "Tue, 24 Oct 2000 07:13:00 -0700",
      From: "phillip.allen@enron.com",
      To: "randall.gay@enron.com",
      Subject: "Promotion changes",
      Body: "Thoughts on changes for next quarter.",
      Categories: ["Salary & Promotion"],
    },
  ]
export const mockNotifications = [
  { id: "1", text: "Notification 1" },
  { id: "2", text: "Notification 2" },
  { id: "3", text: "Notification 3" }
];

export const mockPriorityLevels :  PriorityLevels = {
  Actions: 90,
  Threads: 60,
  Informations: 30
};