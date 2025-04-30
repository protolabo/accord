// Service de débogage pour tracer le flux de données
class DebugService {
  static logEmailCategories(emails: any[]) {
    console.log("=== ANALYSE DES CATÉGORIES D'EMAILS ===");

    // Compter les emails par catégorie principale
    const categoryCounts: {[key: string]: number} = {
      "Actions": 0,
      "Threads": 0,
      "Informations": 0,
      "Non classifié": 0
    };

    // Compter les sous-catégories des Threads
    const threadSubCategories: {[key: string]: number} = {};

    emails.forEach(email => {
      // Compter par catégorie principale
      if (Array.isArray(email.Categories)) {
        email.Categories.forEach((cat: string) => {
          if (categoryCounts[cat] !== undefined) {
            categoryCounts[cat]++;
          } else if (cat === "Actions" || cat === "Threads" || cat === "Informations") {
            categoryCounts[cat] = 1;
          } else {
            // Pourrait être une sous-catégorie
            if (email.Categories.includes("Threads")) {
              threadSubCategories[cat] = (threadSubCategories[cat] || 0) + 1;
            }
          }
        });
      }

      // Si aucune catégorie n'est trouvée
      if (!Array.isArray(email.Categories) || email.Categories.length === 0) {
        categoryCounts["Non classifié"]++;
      }
    });

    console.log("Nombre d'emails par catégorie principale:");
    console.table(categoryCounts);

    console.log("Nombre d'emails par sous-catégorie de Threads:");
    console.table(threadSubCategories);
  }

  static logDataFlow(message: string, data: any) {
    console.log(`=== DEBUG: ${message} ===`);
    if (Array.isArray(data)) {
      console.log(`Nombre d'éléments: ${data.length}`);
      if (data.length > 0) {
        console.log("Premier élément:", data[0]);
      }
    } else {
      console.log(data);
    }
  }
}

export default DebugService;