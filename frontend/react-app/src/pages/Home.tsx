import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import ThreadDetail from "../components/ThreadDetail";
import HomeContent from "./HomeContent";
import emailAPIService from "../services/EmailService";
import { mockEmails, mockNotifications } from "../data/mockData";
import { Email } from "../components/types";
import axios from "axios";
import DebugService from '../services/DebugService';


interface ExtendedEmail extends Email {
  accord_sub_classes?: Array<[string, number]>;
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
    timeBlock: number;
    endTime: Date | null;
  };
  isAuthenticated: boolean;
  emails: ExtendedEmail[];
  isLoading: boolean;
}

interface BackendEmailData {
  "Message-ID"?: string;
  id?: string;
  Subject?: string;
  From?: string;
  To?: string;
  Date?: string;
  Body?: string | { plain?: string; html?: string };
  Categories?: string[];
  accord_main_class?: string;
  accord_sub_classes?: Array<[string, number]>;
  IsRead?: boolean;
  Attachments?: Array<{
    filename?: string;
    contentType?: string;
    content_type?: string; // Backend might use snake_case
    size?: number;
    contentId?: string;
    content_id?: string; // Backend might use snake_case
    url?: string;
  }>;
}

const typedMockEmails = mockEmails as unknown as ExtendedEmail[];

const Home: React.FC = () => {
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

  // First, add this state to track if we've attempted auth
  const [authAttempted, setAuthAttempted] = useState(false);

  useEffect(() => {
  console.log("Home component mounted");

  const loadData = async () => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const userEmail = localStorage.getItem('userEmail');

      await fetchEmails();
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  loadData();
}, []);

  // Fetch emails from the selected email service or classified emails
  const fetchEmails = async () => {
  setState((prev) => ({ ...prev, isLoading: true }));
  try {
    console.log("Récupération des emails...");

    // Récupérer les emails mockés directement
    const mockEmailsResponse = await emailAPIService.getClassifiedEmails();
    const emailsData = mockEmailsResponse.emails;

    console.log(`${emailsData.length} emails récupérés`);

    // Convertir les emails au format attendu par l'interface
    const convertedEmails: ExtendedEmail[] = emailsData.map((email: any) => {
      // Déterminer les catégories
      let categories: string[] = [];

      // Si accord_main_class est un tableau, l'utiliser directement
      if (Array.isArray(email.accord_main_class)) {
        categories = [...email.accord_main_class];
      }
      // Si accord_main_class est une chaîne, la convertir en tableau
      else if (typeof email.accord_main_class === 'string') {
        categories = [email.accord_main_class];
      }
      // Utiliser les catégories existantes si disponibles
      else if (Array.isArray(email.Categories) && email.Categories.length > 0) {
        categories = [...email.Categories];
      }
      // Catégorie par défaut
      else {
        categories = ["Non classifié"];
      }

      // Pour les Threads, ajouter la sous-catégorie avec le score le plus élevé
      if (categories.includes("Threads") && Array.isArray(email.accord_sub_classes) && email.accord_sub_classes.length > 0) {
        // Trouver la sous-catégorie avec le score le plus élevé
        email.accord_sub_classes.sort((a: [string, number], b: [string, number]) => b[1] - a[1]);
        const topSubCategory = email.accord_sub_classes[0][0];
        if (!categories.includes(topSubCategory)) {
          categories.push(topSubCategory);
        }
      }

      return {
        "Message-ID": email["Message-ID"] || email.id || String(Math.random()),
        Subject: email.Subject || "Sans objet",
        From: email.From || "inconnu@example.com",
        To: email.To || "",
        Cc: email.Cc || "",
        Date: email.Date || new Date().toISOString(),
        "Content-Type": email["Content-Type"] || "text/plain",
        Body: typeof email.Body === 'string' ? email.Body :
              (email.Body?.plain || email.Body?.html || ""),
        IsRead: email.IsRead || false,
        Attachments: (email.Attachments || []).map((att: any) => ({
          filename: att.filename || "pièce jointe",
          contentType: att.contentType || att.content_type || "application/octet-stream",
          size: att.size || 0,
          contentId: att.contentId || att.content_id || "",
          url: att.url || ""
        })),
        Categories: categories,
        Importance: "normal",
        ThreadId: email.ThreadId || email["Thread-ID"] || email["Message-ID"] || String(Math.random()),
        accord_sub_classes: email.accord_sub_classes
      };
    });

    console.log("Emails convertis:", convertedEmails.length);

    // le débogage
    DebugService.logEmailCategories(convertedEmails);

    setState((prev) => ({
      ...prev,
      emails: convertedEmails,
      isLoading: false,
    }));
  } catch (error) {
    console.error("Erreur lors de la récupération des emails:", error);
    setState((prev) => ({
      ...prev,
      emails: [],
      isLoading: false
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

  // Groupe les emails par catégorie principale et sous-catégorie
  const groupEmailsByCategory = (emails: Email[]) => {
  const grouped: { [key: string]: Email[] } = {};

  // D'abord, ajouter tous les emails à leurs catégories principales
  emails.forEach((email) => {
    email.Categories.forEach((category) => {
      if (!grouped[category]) {
        grouped[category] = [];
      }

      // Éviter les doublons
      if (!grouped[category].some(e => e["Message-ID"] === email["Message-ID"])) {
        grouped[category].push(email);
      }
    });
  });

  // Pour les emails de type Threads, les ajouter également à leurs sous-catégories
  emails.forEach((email) => {
    if (email.Categories.includes("Threads") &&
        email.accord_sub_classes &&
        email.accord_sub_classes.length > 0) {

      // Prendre la sous-catégorie avec le score le plus élevé
      const topSubCategory = email.accord_sub_classes[0][0];

      if (!grouped[topSubCategory]) {
        grouped[topSubCategory] = [];
      }

      // Éviter les doublons
      if (!grouped[topSubCategory].some(e => e["Message-ID"] === email["Message-ID"])) {
        grouped[topSubCategory].push(email);
      }
    }
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
        {state.showThreadDetail ? (
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