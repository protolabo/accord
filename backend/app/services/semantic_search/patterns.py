"""
Patterns enrichis multilingues pour l'extraction d'entités et la détection d'intention.
Supporte français et anglais avec fallback automatique.
"""

from typing import Dict, Any, List



class EmailPatterns:
    """Gestionnaire centralisé de tous les patterns email"""

    def __init__(self):
        self._init_temporal_patterns()
        self._init_contact_patterns()
        self._init_topic_patterns()
        self._init_action_patterns()
        self._init_intent_patterns()
        self._init_validation_patterns()

    def _init_temporal_patterns(self):
        """Patterns pour détection temporelle enrichie"""
        self.temporal_patterns = {
            'fr': {
                # Relatif - Jours
                r'\b(hier|yesterday)\b': {'type': 'relative_day', 'offset': -1},
                r'\b(avant[-\s]?hier)\b': {'type': 'relative_day', 'offset': -2},
                r'\b(aujourd\'hui|ce jour|ajd)\b': {'type': 'relative_day', 'offset': 0},
                r'\b(demain|tomorrow)\b': {'type': 'relative_day', 'offset': 1},
                r'\b(après[-\s]?demain)\b': {'type': 'relative_day', 'offset': 2},

                # Relatif - Semaines
                r'\b(la semaine dernière|semaine passée|semaine précédente)\b': {'type': 'relative_week', 'offset': -1},
                r'\b(cette semaine|semaine en cours)\b': {'type': 'relative_week', 'offset': 0},
                r'\b(la semaine prochaine|semaine suivante)\b': {'type': 'relative_week', 'offset': 1},
                r'\b(il y a (\d+) semaines?)\b': {'type': 'relative_week_number', 'multiplier': -1},
                r'\b(dans (\d+) semaines?)\b': {'type': 'relative_week_number', 'multiplier': 1},

                # Relatif - Mois
                r'\b(le mois dernier|mois passé|mois précédent)\b': {'type': 'relative_month', 'offset': -1},
                r'\b(ce mois|mois en cours)\b': {'type': 'relative_month', 'offset': 0},
                r'\b(le mois prochain|mois suivant)\b': {'type': 'relative_month', 'offset': 1},
                r'\b(il y a (\d+) mois)\b': {'type': 'relative_month_number', 'multiplier': -1},
                r'\b(dans (\d+) mois)\b': {'type': 'relative_month_number', 'multiplier': 1},

                # Relatif - Années
                r'\b(l\'année dernière|année passée|an dernier)\b': {'type': 'relative_year', 'offset': -1},
                r'\b(cette année|année en cours)\b': {'type': 'relative_year', 'offset': 0},
                r'\b(l\'année prochaine|année suivante|an prochain)\b': {'type': 'relative_year', 'offset': 1},

                # Périodes
                r'\b(récemment|dernièrement)\b': {'type': 'recent', 'days': -7},
                r'\b(bientôt|prochainement)\b': {'type': 'soon', 'days': 7},
                r'\b(maintenant|en ce moment)\b': {'type': 'now', 'offset': 0},

                # Jours de la semaine
                r'\b(lundi|monday)\b': {'type': 'weekday', 'day': 0},
                r'\b(mardi|tuesday)\b': {'type': 'weekday', 'day': 1},
                r'\b(mercredi|wednesday)\b': {'type': 'weekday', 'day': 2},
                r'\b(jeudi|thursday)\b': {'type': 'weekday', 'day': 3},
                r'\b(vendredi|friday)\b': {'type': 'weekday', 'day': 4},
                r'\b(samedi|saturday)\b': {'type': 'weekday', 'day': 5},
                r'\b(dimanche|sunday)\b': {'type': 'weekday', 'day': 6},

                # Mois
                r'\b(janvier|january|jan)\b': {'type': 'month', 'month': 1},
                r'\b(février|february|feb|fév)\b': {'type': 'month', 'month': 2},
                r'\b(mars|march|mar)\b': {'type': 'month', 'month': 3},
                r'\b(avril|april|apr|avr)\b': {'type': 'month', 'month': 4},
                r'\b(mai|may)\b': {'type': 'month', 'month': 5},
                r'\b(juin|june|jun)\b': {'type': 'month', 'month': 6},
                r'\b(juillet|july|jul)\b': {'type': 'month', 'month': 7},
                r'\b(août|august|aug|aout)\b': {'type': 'month', 'month': 8},
                r'\b(septembre|september|sep|sept)\b': {'type': 'month', 'month': 9},
                r'\b(octobre|october|oct)\b': {'type': 'month', 'month': 10},
                r'\b(novembre|november|nov)\b': {'type': 'month', 'month': 11},
                r'\b(décembre|december|dec|déc)\b': {'type': 'month', 'month': 12},

                # Formats de dates
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b': {'type': 'absolute_date_fr'},
                r'\b(\d{1,2})[-.](\d{1,2})[-.](\d{4})\b': {'type': 'absolute_date_fr'},
                r'\b(\d{4})-(\d{2})-(\d{2})\b': {'type': 'iso_date'},
                r'\b(\d{1,2}) (janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) (\d{4})\b': {
                    'type': 'date_text_fr'},
            },

            'en': {
                # Relatif - Jours
                r'\b(yesterday)\b': {'type': 'relative_day', 'offset': -1},
                r'\b(today)\b': {'type': 'relative_day', 'offset': 0},
                r'\b(tomorrow)\b': {'type': 'relative_day', 'offset': 1},
                r'\b(day before yesterday)\b': {'type': 'relative_day', 'offset': -2},
                r'\b(day after tomorrow)\b': {'type': 'relative_day', 'offset': 2},

                # Relatif - Semaines
                r'\b(last week|previous week)\b': {'type': 'relative_week', 'offset': -1},
                r'\b(this week|current week)\b': {'type': 'relative_week', 'offset': 0},
                r'\b(next week|following week)\b': {'type': 'relative_week', 'offset': 1},
                r'\b((\d+) weeks? ago)\b': {'type': 'relative_week_number', 'multiplier': -1},
                r'\b(in (\d+) weeks?)\b': {'type': 'relative_week_number', 'multiplier': 1},

                # Relatif - Mois
                r'\b(last month|previous month)\b': {'type': 'relative_month', 'offset': -1},
                r'\b(this month|current month)\b': {'type': 'relative_month', 'offset': 0},
                r'\b(next month|following month)\b': {'type': 'relative_month', 'offset': 1},
                r'\b((\d+) months? ago)\b': {'type': 'relative_month_number', 'multiplier': -1},
                r'\b(in (\d+) months?)\b': {'type': 'relative_month_number', 'multiplier': 1},

                # Périodes
                r'\b(recently|lately)\b': {'type': 'recent', 'days': -7},
                r'\b(soon|shortly)\b': {'type': 'soon', 'days': 7},
                r'\b(now|currently)\b': {'type': 'now', 'offset': 0},

                # Formats dates US
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b': {'type': 'absolute_date_us'},
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december) (\d{1,2}),? (\d{4})\b': {
                    'type': 'date_text_en'},
            }
        }

    def _init_contact_patterns(self):
        """Patterns pour détection de contacts enrichie"""
        self.contact_patterns = {
            'fr': {
                # Expéditeur
                r'\b(de|from|par|by|expéditeur|sender|envoyé par)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'from_contact',
                r'\b(emails?\s+de|mails?\s+de|messages?\s+de|courriels?\s+de)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'from_contact',
                r'\b(reçu de|provenant de|venant de)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'from_contact',

                # Destinataire
                r'\b(à|to|pour|destinataire|envoyé à)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'to_contact',
                r'\b(emails?\s+à|mails?\s+à|messages?\s+à)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'to_contact',

                # Email addresses
                r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b': 'email_address',

                # Groupes/organisations
                r'\b(équipe|team|groupe|group|département|dept)\s+([A-Z][a-zA-Z\s]{2,20})\b': 'group_contact',
                r'\b(société|company|entreprise|firm)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'company_contact',

                # Domaines emails
                r'\b(domaine|domain)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b': 'email_domain',
                r'\b(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b': 'email_domain',
            },

            'en': {
                # Expéditeur
                r'\b(from|by|sender|sent by)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'from_contact',
                r'\b(emails?\s+from|mails?\s+from|messages?\s+from)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'from_contact',
                r'\b(received from|coming from)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'from_contact',

                # Destinataire
                r'\b(to|for|recipient|sent to)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'to_contact',
                r'\b(emails?\s+to|mails?\s+to|messages?\s+to)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'to_contact',

                # Groupes
                r'\b(team|group|department|dept)\s+([A-Z][a-zA-Z\s]{2,20})\b': 'group_contact',
                r'\b(company|firm|organization|org)\s+([A-Z][a-zA-Z\s.-]{2,30})\b': 'company_contact',
            }
        }

    def _init_topic_patterns(self):
        """Patterns pour détection de sujets/topics enrichie"""
        self.topic_patterns = {
            'fr': {
                # Finances
                r'\b(facture|invoice|bill|facturation|billing)\b': 'facturation',
                r'\b(paiement|payment|pay|règlement|settlement)\b': 'payment',
                r'\b(devis|quote|estimation|budget)\b': 'devis',
                r'\b(commande|order|achat|purchase)\b': 'commande',
                r'\b(remboursement|refund|reimbursement)\b': 'remboursement',

                # Confirmations/Notifications
                r'\b(confirmation|confirmé|confirmed|validate)\b': 'confirmation',
                r'\b(notification|alert|alerte|rappel|reminder)\b': 'notification',
                r'\b(reçu|receipt|accusé de réception)\b': 'receipt',

                # Communications
                r'\b(newsletter|bulletin|actualités|news)\b': 'newsletter',
                r'\b(promotion|promo|offer|offre|discount|réduction)\b': 'promotion',
                r'\b(publicité|advertising|ad|pub|marketing)\b': 'publicite',
                r'\b(spam|indésirable|junk)\b': 'spam',

                # Livraison/Shipping
                r'\b(shipping|expédition|livraison|delivery|transport)\b': 'livraison',
                r'\b(suivi|tracking|trace|traçage)\b': 'tracking',
                r'\b(colis|package|paquet|parcel)\b': 'colis',

                # Travail/Business
                r'\b(meeting|réunion|rendez[-\s]?vous|appointment|rdv)\b': 'meeting',
                r'\b(projet|project|task|tâche|mission)\b': 'projet',
                r'\b(rapport|report|summary|résumé|compte[-\s]?rendu)\b': 'rapport',
                r'\b(contrat|contract|agreement|accord)\b': 'contrat',

                # Urgence/Priorité
                r'\b(urgent|emergency|urgence|priorité|priority)\b': 'urgent',
                r'\b(important|critical|critique|essentiel)\b': 'important',
                r'\b(deadline|échéance|date limite|due date)\b': 'deadline',

                # Réseaux sociaux
                r'\b(social|réseau|network|facebook|linkedin|twitter|instagram)\b': 'social',
                r'\b(notification sociale|social notification)\b': 'social_notification',

                # Support/Service
                r'\b(support|aide|help|assistance|service client)\b': 'support',
                r'\b(bug|erreur|error|problème|issue)\b': 'support_technique',

                # Sécurité
                r'\b(sécurité|security|mot de passe|password|login|connexion)\b': 'security',
                r'\b(authentification|authentication|verification|vérification)\b': 'auth',
                r'\b(compte|account|profil|profile)\b': 'account',
            },

            'en': {
                # Finances
                r'\b(invoice|bill|billing|payment|receipt)\b': 'billing',
                r'\b(quote|estimate|budget|cost)\b': 'quote',
                r'\b(order|purchase|buy|transaction)\b': 'order',
                r'\b(refund|reimbursement|credit)\b': 'refund',

                # Communications
                r'\b(newsletter|news|update|announcement)\b': 'newsletter',
                r'\b(promotion|promo|offer|deal|discount|sale)\b': 'promotion',
                r'\b(advertisement|advertising|ad|marketing)\b': 'advertisement',

                # Work/Business
                r'\b(meeting|appointment|conference|call)\b': 'meeting',
                r'\b(project|task|assignment|job)\b': 'project',
                r'\b(report|summary|update|status)\b': 'report',
                r'\b(contract|agreement|proposal)\b': 'contract',

                # Urgency
                r'\b(urgent|emergency|critical|important)\b': 'urgent',
                r'\b(deadline|due date|timeline)\b': 'deadline',

                # Support
                r'\b(support|help|assistance|service)\b': 'support',
                r'\b(bug|error|issue|problem|trouble)\b': 'technical_support',
            }
        }

    def _init_action_patterns(self):
        """Patterns pour détection d'actions enrichie"""
        self.action_patterns = {
            'fr': {
                # Pièces jointes
                r'\b(avec|with)\s+(pièce jointe|attachment|fichier|file|document)\b': 'has_attachment',
                r'\b(pièces? jointes?|attachments?|fichiers?|documents?)\b': 'has_attachment',
                r'\b(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|jpg|png|gif)\b': 'has_attachment',

                # Conversations/Threads
                r'\b(dans|in)\s+(conversation|thread|fil|discussion|échange)\b': 'in_thread',
                r'\b(conversations?|threads?|fils?|discussions?|échanges?)\b': 'in_thread',
                r'\b(réponse à|reply to|re:|fw:)\b': 'in_thread',

                # États des emails
                r'\b(non lu|unread|pas lu|new)\b': 'unread',
                r'\b(lu|read|opened|ouvert)\b': 'read',
                r'\b(important|starred|étoilé|favori|favorite)\b': 'important',
                r'\b(archivé|archived|archive)\b': 'archived',
                r'\b(supprimé|deleted|trash|corbeille)\b': 'deleted',
                r'\b(brouillon|draft|drafts)\b': 'draft',
                r'\b(envoyé|sent|expedié)\b': 'sent',

                # Actions utilisateur
                r'\b(marqué|marked|tagged|étiqueté)\b': 'tagged',
                r'\b(transféré|forwarded|forward|fw)\b': 'forwarded',
                r'\b(répondu|replied|answered)\b': 'replied',

                # Filtres avancés
                r'\b(sans|without|excluding|excluant)\b': 'exclude',
                r'\b(seulement|only|uniquement|just)\b': 'only',
                r'\b(contenant|containing|avec le mot|with word)\b': 'contains',
            },

            'en': {
                # Attachments
                r'\b(with|having)\s+(attachment|file|document)\b': 'has_attachment',
                r'\b(attachments?|files?|documents?)\b': 'has_attachment',

                # Threads
                r'\b(in|within)\s+(conversation|thread|discussion)\b': 'in_thread',
                r'\b(conversations?|threads?|discussions?)\b': 'in_thread',

                # Email states
                r'\b(unread|new)\b': 'unread',
                r'\b(read|opened)\b': 'read',
                r'\b(important|starred|favorite)\b': 'important',
                r'\b(archived|archive)\b': 'archived',
                r'\b(deleted|trash)\b': 'deleted',
                r'\b(draft|drafts)\b': 'draft',
                r'\b(sent|outgoing)\b': 'sent',

                # User actions
                r'\b(marked|tagged|labeled)\b': 'tagged',
                r'\b(forwarded|forward)\b': 'forwarded',
                r'\b(replied|answered)\b': 'replied',
            }
        }

    def _init_intent_patterns(self):
        """Patterns pour détection d'intention globale"""
        self.intent_patterns = {
            'search_contact': {
                'fr': [
                    r'\b(emails?\s+de|mails?\s+de|messages?\s+de)',
                    r'\b(expéditeur|sender|from|de)',
                    r'@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    r'\b(reçu de|provenant de|venant de)',
                ],
                'en': [
                    r'\b(emails?\s+from|mails?\s+from|messages?\s+from)',
                    r'\b(sender|from)',
                    r'@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    r'\b(received from|from)',
                ]
            },

            'search_temporal': {
                'fr': [
                    r'\b(hier|aujourd|semaine|mois|année)',
                    r'\d{1,2}/\d{1,2}/\d{4}',
                    r'\b(récent|recent|latest|dernier)',
                    r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)',
                ],
                'en': [
                    r'\b(yesterday|today|week|month|year)',
                    r'\d{1,2}/\d{1,2}/\d{4}',
                    r'\b(recent|latest|last)',
                    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)',
                ]
            },

            'search_attachment': {
                'fr': [
                    r'\b(avec|with)\s+(pièce|attachment|fichier|file)',
                    r'\b(pdf|doc|image|photo|document)',
                    r'\b(pièces? jointes?|fichiers? joints?)',
                ],
                'en': [
                    r'\b(with|having)\s+(attachment|file|document)',
                    r'\b(pdf|doc|image|photo|document)',
                    r'\b(attachments?|files?)',
                ]
            },

            'search_thread': {
                'fr': [
                    r'\b(conversation|thread|fil|discussion)',
                    r'\b(échange|dialogue|correspondance)',
                    r'\b(réponse|reply|re:)',
                ],
                'en': [
                    r'\b(conversation|thread|discussion)',
                    r'\b(exchange|dialogue|correspondence)',
                    r'\b(reply|response|re:)',
                ]
            }
        }

    def _init_validation_patterns(self):
        """Patterns pour validation et nettoyage"""
        self.validation_patterns = {
            'blacklist_names': {
                'fr': ['test', 'exemple', 'debug', 'demo', 'sample', 'foo', 'bar', 'lorem', 'ipsum'],
                'en': ['test', 'example', 'debug', 'demo', 'sample', 'foo', 'bar', 'lorem', 'ipsum']
            },

            'common_domains': [
                'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'free.fr',
                'orange.fr', 'wanadoo.fr', 'laposte.net', 'sfr.fr'
            ],

            'stopwords': {
                'fr': [
                    'emails?', 'mails?', 'messages?', 'courriels?', 'de', 'du', 'des',
                    'le', 'la', 'les', 'avec', 'sans', 'dans', 'par', 'pour', 'sur',
                    'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car'
                ],
                'en': [
                    'emails?', 'mails?', 'messages?', 'from', 'to', 'with', 'without',
                    'in', 'by', 'for', 'on', 'and', 'or', 'but', 'the', 'a', 'an'
                ]
            }
        }

    def get_patterns(self, language: str = 'auto', category: str = 'all') -> Dict[str, Any]:
        """
        Récupère les patterns selon la langue et la catégorie

        Args:
            language: 'fr', 'en', ou 'auto' pour combiner
            category: 'temporal', 'contact', 'topic', 'action', 'intent', 'validation', ou 'all'

        Returns:
            Dictionnaire des patterns demandés
        """
        patterns = {}

        # Sélection des catégories
        categories = {
            'temporal': self.temporal_patterns,
            'contact': self.contact_patterns,
            'topic': self.topic_patterns,
            'action': self.action_patterns,
            'intent': self.intent_patterns,
            'validation': self.validation_patterns
        }

        if category == 'all':
            selected_categories = categories
        else:
            selected_categories = {category: categories.get(category, {})}

        # Fusion selon la langue
        for cat_name, cat_patterns in selected_categories.items():
            if language == 'auto':
                # Combine FR + EN
                combined = {}
                if isinstance(cat_patterns, dict):
                    for lang in ['fr', 'en']:
                        if lang in cat_patterns:
                            if isinstance(cat_patterns[lang], dict):
                                combined.update(cat_patterns[lang])
                            else:
                                combined[lang] = cat_patterns[lang]
                patterns[cat_name] = combined
            else:
                # Langue spécifique
                if isinstance(cat_patterns, dict) and language in cat_patterns:
                    patterns[cat_name] = cat_patterns[language]
                else:
                    patterns[cat_name] = cat_patterns

        return patterns

    def is_blacklisted_name(self, name: str, language: str = 'auto') -> bool:
        """Vérifie si un nom est dans la blacklist"""
        blacklist = []
        if language == 'auto':
            blacklist.extend(self.validation_patterns['blacklist_names']['fr'])
            blacklist.extend(self.validation_patterns['blacklist_names']['en'])
        else:
            blacklist = self.validation_patterns['blacklist_names'].get(language, [])

        return name.lower() in blacklist

    def get_stopwords(self, language: str = 'auto') -> List[str]:
        """Récupère les mots vides selon la langue"""
        if language == 'auto':
            stopwords = []
            stopwords.extend(self.validation_patterns['stopwords']['fr'])
            stopwords.extend(self.validation_patterns['stopwords']['en'])
            return stopwords
        else:
            return self.validation_patterns['stopwords'].get(language, [])


# Instance globale singleton
_email_patterns: EmailPatterns = None


def get_email_patterns() -> EmailPatterns:
    """Récupère l'instance singleton des patterns"""
    global _email_patterns
    if _email_patterns is None:
        _email_patterns = EmailPatterns()
    return _email_patterns


# Fonctions utilitaires pour compatibilité
def get_patterns(language: str = 'auto', category: str = 'all') -> Dict[str, Any]:
    """Fonction utilitaire pour récupérer les patterns"""
    return get_email_patterns().get_patterns(language, category)


def is_blacklisted_name(name: str, language: str = 'auto') -> bool:
    """Fonction utilitaire pour vérifier la blacklist"""
    return get_email_patterns().is_blacklisted_name(name, language)


def get_stopwords(language: str = 'auto') -> List[str]:
    """Fonction utilitaire pour récupérer les stopwords"""
    return get_email_patterns().get_stopwords(language)


