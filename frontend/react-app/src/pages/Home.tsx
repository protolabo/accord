import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import EmailLogin from "../components/EmailLogin";
import ThreadDetail from "../components/ThreadDetail";
import HomeContent from "./HomeContent";
import emailAPIService from "../services/EmailService";
import { mockEmails, mockNotifications } from "../data/mockData";

// Define Email interface for the component
interface Email {
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

interface HomeState {
  searchTerm: string;
  darkMode: boolean;
  availability: number;
  sectionSizes: {
    [key: string]: number;
  };
  isAvailable: boolean;
  showNotifications: boolean;
  showProfileOptions: boolean;
  selectedThread: Email | null;
  showThreadDetail: boolean;
  isResizing: boolean;
  resizingIndex: number | null;
  startX: number;
  startSizes: { [key: string]: number };
  showSearchPopup: boolean;
  focusMode: {
    active: boolean;
    priority: "high" | "medium" | "low";
    timeBlock: number; // minutes
    endTime: Date | null;
  };
  isAuthenticated: boolean;
  emails: Email[];
  isLoading: boolean;
}

// Add type cast to ensure mockEmails matches our Email interface
const typedMockEmails = mockEmails as unknown as Email[];

const Home: React.FC = () => {
  // Initial state
  const initialState: HomeState = {
    searchTerm: "",
    darkMode: false,
    availability: 50,
    sectionSizes: {
      Actions: 1,
      Threads: 1,
      Informations: 1,
    },
    isAvailable: true,
    showNotifications: false,
    showProfileOptions: false,
    selectedThread: null,
    showThreadDetail: false,
    isResizing: false,
    resizingIndex: null,
    startX: 0,
    startSizes: {},
    showSearchPopup: false,
    focusMode: {
      active: false,
      priority: "high",
      timeBlock: 25,
      endTime: null,
    },
    isAuthenticated: false,
    emails: [],
    isLoading: false,
  };

  const [state, setState] = useState<HomeState>(initialState);
  const navigate = useNavigate();

  //  ##### A decommenter
useEffect(() => {
  const checkAuth = async () => {
    try {
      // Vérifier l'état d'authentification depuis le backend
      const response = await fetch('/auth/status', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const authData = await response.json();

        setState((prev) => ({
          ...prev,
          isAuthenticated: authData.authenticated,
          userEmail: authData.email || ''
        }));

        // Si l'utilisateur est authentifié, récupérer les emails
        if (authData.authenticated) {
          fetchEmails();
        }
      } else {
        setState((prev) => ({ ...prev, isAuthenticated: false }));
      }
    } catch (error) {
      console.error('Erreur lors de la vérification de l\'authentification:', error);
      setState((prev) => ({ ...prev, isAuthenticated: false }));
    }
  };
  //setState((prev) => ({ ...prev, isAuthenticated: true }));
  //fetchEmails();
  // Appeler la fonction de vérification
  checkAuth();
}, []);



  // Fetch emails from the selected email service or classified emails
  const fetchEmails = async () => {
  setState((prev) => ({ ...prev, isLoading: true }));

  try {
    // Vérifier d'abord s'il y a des emails classifiés disponibles
    const classificationStatus =
      await emailAPIService.checkClassificationStatus();

    if (classificationStatus.status === "completed") {
      // Des emails classifiés sont disponibles, les récupérer
      const classifiedEmailsResponse =
        await emailAPIService.getClassifiedEmails();

      // Convertir les emails classifiés au format attendu par l'interface
      const convertedEmails: Email[] = classifiedEmailsResponse.emails.map(
        (email: any) => ({
          "Message-ID":
            email["Message-ID"] || email.id || String(Math.random()),
          Subject: email.Subject || "Sans objet",
          From: email.From || "inconnu@example.com",
          To: email.To || "",
          Cc: email.Cc || "",
          Date: email.Date || new Date().toISOString(),
          "Content-Type": email["Content-Type"] || "text/plain",
          Body: email.Body?.plain || email.Body?.html || email.Body || "",
          IsRead: email.IsRead || false,
          // Conversion des attachements pour correspondre à l'interface
          Attachments: (email.Attachments || []).map((att: any) => ({
            filename: att.filename,
            contentType: att.content_type, // Transformé
            size: att.size,
            contentId: att.content_id, // Transformé
            url: att.url
          })),
          Categories: email.accord_main_class
            ? [email.accord_main_class, ...(email.accord_sub_classes || [])]
            : ["Non classifié"],
          Importance: "normal",
          ThreadId:
            email.ThreadId ||
            email["Thread-ID"] ||
            email["Message-ID"] ||
            String(Math.random()),
        })
      );

      setState((prev) => ({
        ...prev,
        emails: convertedEmails,
        isLoading: false,
      }));

      console.log("Emails classifiés chargés:", convertedEmails.length);
      return;
    }

    // Si pas d'emails classifiés, essayer l'API normale
    if (emailAPIService.isAuthenticated()) {
      const response = await emailAPIService.fetchEmails(); // Stocké dans 'response'

      // Convert service emails to the format expected by the app
      const convertedEmails: Email[] = response.map((email: any) => ({
        "Message-ID": email.id,
        Subject: email.subject,
        From: email.from,
        To: email.to.join(", "),
        Cc: email.cc.join(", "),
        Date: email.date.toString(),
        "Content-Type":
          email.bodyType === "html" ? "text/html" : "text/plain",
        Body: email.body,
        IsRead: email.isRead,
        // Conversion des attachements
        Attachments: (email.attachments || []).map((att: any) => ({
          filename: att.filename,
          contentType: att.content_type,
          size: att.size,
          contentId: att.content_id,
          url: att.url
        })),
        Categories: email.categories,
        Importance: email.isImportant ? "high" : "normal",
        ThreadId: email.threadId || email.id,
      }));

      setState((prev) => ({
        ...prev,
        emails: convertedEmails,
        isLoading: false,
      }));
    } else {
      // Fall back to mock data if not authenticated
      setState((prev) => ({
        ...prev,
        emails: typedMockEmails,
        isLoading: false,
      }));
    }
  } catch (error) {
    console.error("Error fetching emails:", error);
    // Fall back to mock data on error
    setState((prev) => ({
      ...prev,
      emails: typedMockEmails,
      isLoading: false,
    }));
  }
};

  // Handle successful login
  const handleLoginSuccess = () => {
    setState((prev) => ({ ...prev, isAuthenticated: true }));
    fetchEmails();
  };

  // Effect for dark mode
  useEffect(() => {
    if (state.darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [state.darkMode]);

  // Filter emails
  const filteredEmails = state.emails.filter(
    (email) =>
      email.Subject.toLowerCase().includes(state.searchTerm.toLowerCase()) ||
      email.From.toLowerCase().includes(state.searchTerm.toLowerCase())
  );

  // Group emails by category
  const groupEmailsByCategory = (emails: Email[]) => {
    const grouped: { [key: string]: Email[] } = {};
    emails.forEach((email) => {
      email.Categories.forEach((category) => {
        if (!grouped[category]) {
          grouped[category] = [];
        }
        grouped[category].push(email);
      });
    });
    return grouped;
  };

  const groupedEmails = groupEmailsByCategory(state.emails);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setState((prev) => ({ ...prev, searchTerm: e.target.value }));
  };

  const handleSearchClick = () => {
    setState((prev) => ({ ...prev, showSearchPopup: true }));
  };

  const toggleDarkMode = () => {
    setState((prev) => ({ ...prev, darkMode: !prev.darkMode }));
  };

  const toggleAvailability = () => {
    setState((prev) => ({ ...prev, isAvailable: !prev.isAvailable }));
  };

  const toggleNotifications = () => {
    setState((prev) => ({
      ...prev,
      showNotifications: !prev.showNotifications,
    }));
  };

  const toggleProfileOptions = () => {
    setState((prev) => ({
      ...prev,
      showProfileOptions: !prev.showProfileOptions,
    }));
  };

  // resize section
  const handleSectionResize = (
    sectionName: string,
    action: "expand" | "collapse" | "reset"
  ) => {
    setState((prev) => {
      const newSizes = { ...prev.sectionSizes };

      if (action === "expand") {
        Object.keys(newSizes).forEach((key) => {
          if (key === sectionName) {
            newSizes[key] = 2;
          } else {
            newSizes[key] = 0.5;
          }
        });
      } else if (action === "collapse") {
        newSizes[sectionName] = 0.5;

        // Adjust other sections
        const otherSections = Object.keys(newSizes).filter(
          (k) => k !== sectionName
        );
        otherSections.forEach((key) => {
          newSizes[key] = 1.25;
        });
      } else {
        // Reset all sections to equal size
        Object.keys(newSizes).forEach((key) => {
          newSizes[key] = 1;
        });
      }

      return { ...prev, sectionSizes: newSizes };
    });
  };

  const handleThreadSelect = useCallback(async (email: Email) => {
    setState((prev) => ({
      ...prev,
      selectedThread: email,
      showThreadDetail: true,
    }));

    // Mark as read if using real email service
    if (emailAPIService.isAuthenticated() && email && !email.IsRead) {
      try {
        await emailAPIService.markAsRead(email["Message-ID"]);
        // Update the email in state to reflect it's now read
        setState((prev) => ({
          ...prev,
          emails: prev.emails.map((e) =>
            e["Message-ID"] === email["Message-ID"] ? { ...e, IsRead: true } : e
          ),
        }));
      } catch (error) {
        console.error("Error marking email as read:", error);
      }
    }
  }, []);

  const handleBackToList = () => {
    setState((prev) => ({
      ...prev,
      selectedThread: null,
      showThreadDetail: false,
    }));
  };

  // resize event handlers
  const handleResizeStart = useCallback(
    (index: number, clientX: number) => {
      const sectionSizes = { ...state.sectionSizes };

      setState((prev) => ({
        ...prev,
        isResizing: true,
        resizingIndex: index,
        startX: clientX,
        startSizes: { ...sectionSizes },
      }));
    },
    [state.sectionSizes]
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!state.isResizing || state.resizingIndex === null) return;

      const deltaX = e.clientX - state.startX;

      if (Math.abs(deltaX) < 5) return;

      const containerWidth = 1000; // Using a default width
      const deltaRatio = deltaX / containerWidth;

      const sectionKeys = Object.keys(state.sectionSizes);
      const leftSection = sectionKeys[state.resizingIndex];
      const rightSection = sectionKeys[state.resizingIndex + 1];

      if (!leftSection || !rightSection) return;

      // minimum size
      const MIN_SIZE = 0.15;
      const newSizes = { ...state.startSizes };

      const totalCurrentSize = newSizes[leftSection] + newSizes[rightSection];

      let newLeftSize = newSizes[leftSection] + deltaRatio * totalCurrentSize;
      let newRightSize = newSizes[rightSection] - deltaRatio * totalCurrentSize;

      if (newLeftSize < MIN_SIZE) {
        newLeftSize = MIN_SIZE;
        newRightSize = totalCurrentSize - MIN_SIZE;
      } else if (newRightSize < MIN_SIZE) {
        newRightSize = MIN_SIZE;
        newLeftSize = totalCurrentSize - MIN_SIZE;
      }

      newSizes[leftSection] = newLeftSize;
      newSizes[rightSection] = newRightSize;

      setState((prev) => ({
        ...prev,
        sectionSizes: newSizes,
      }));
    },
    [
      state.isResizing,
      state.resizingIndex,
      state.startX,
      state.startSizes,
      state.sectionSizes,
    ]
  );

  const handleMouseUp = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isResizing: false,
      resizingIndex: null,
    }));
  }, []);

  useEffect(() => {
    if (state.isResizing) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [state.isResizing, handleMouseMove, handleMouseUp]);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-200">
      <Header
        showThreadDetail={state.showThreadDetail}
        handleBackToList={handleBackToList}
        searchTerm={state.searchTerm}
        handleSearchChange={handleSearchChange}
        handleSearchClick={handleSearchClick}
        darkMode={state.darkMode}
        toggleDarkMode={toggleDarkMode}
        isAvailable={state.isAvailable}
        toggleAvailability={toggleAvailability}
        showNotifications={state.showNotifications}
        toggleNotifications={toggleNotifications}
        notifications={mockNotifications}
        showProfileOptions={state.showProfileOptions}
        toggleProfileOptions={toggleProfileOptions}
      />

      {/* Main content */}
      <main className="container mx-auto p-4">
        {!state.isAuthenticated ? (
          <EmailLogin onLogin={handleLoginSuccess} />
        ) : state.showThreadDetail ? (
          <ThreadDetail
            thread={state.selectedThread}
            onBack={handleBackToList}
          />
        ) : (
          <HomeContent
            isLoading={state.isLoading}
            sectionSizes={state.sectionSizes}
            isResizing={state.isResizing}
            filteredEmails={filteredEmails}
            handleSectionResize={handleSectionResize}
            handleResizeStart={handleResizeStart}
            handleThreadSelect={handleThreadSelect}
            groupedEmails={groupedEmails}
            showSearchPopup={state.showSearchPopup}
            setShowSearchPopup={(show) => setState(prev => ({ ...prev, showSearchPopup: show }))}
            fetchEmails={fetchEmails}
          />
        )}
      </main>
    </div>
  );
};

export default Home;