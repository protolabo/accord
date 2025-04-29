import React from 'react';
import FrequentContactsPanel from './FrequentContactsPanel';

interface PartialContact {
  id: string | number;
  name: string;
  email: string;
  availability: number;
}

interface Contact {
  id: string;
  name: string;
  email: string;
  availability: number;
  lastContact: string;
}

interface ContactsAdapterProps {
  contacts: PartialContact[];
}


const ContactsAdapter: React.FC<ContactsAdapterProps> = ({ contacts }) => {
  const adaptedContacts: Contact[] = contacts.map(contact => ({
    id: contact.id.toString(),
    name: contact.name,
    email: contact.email,
    availability: contact.availability,
    lastContact: new Date().toISOString()
  }));

  return <FrequentContactsPanel contacts={adaptedContacts} />;
};

export default ContactsAdapter;