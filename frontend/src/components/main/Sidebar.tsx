import React, { createContext, useContext } from "react";
import {
  InboxIcon,
  StarIcon,
  ClockIcon,
  PaperAirplaneIcon,
  DocumentTextIcon,
  TrashIcon,
} from "@heroicons/react/24/outline";

type SidebarContextValue = { expanded: boolean };
const SidebarContext = createContext<SidebarContextValue>({ expanded: true });

interface SidebarItemDef {
  name: string;
  icon: React.ReactNode;
  count?: number;
  active?: boolean;
  alert?: boolean;
}

interface SidebarProps {
  collapsed: boolean;      
}

export default function Sidebar({ collapsed }: SidebarProps) {
  const items: SidebarItemDef[] = [
    { name: "Inbox",   icon: <InboxIcon className="w-5 h-5" />, count: 120, active: true },
    { name: "Starred", icon: <StarIcon className="w-5 h-5" /> },
    { name: "Snoozed", icon: <ClockIcon className="w-5 h-5" /> },
    { name: "Sent",    icon: <PaperAirplaneIcon className="w-5 h-5" /> },
    { name: "Drafts",  icon: <DocumentTextIcon className="w-5 h-5" />, count: 12 },
    { name: "Trash",   icon: <TrashIcon className="w-5 h-5" /> },
  ];

  const expanded = !collapsed;

  return (
    <aside
      className={`h-screen border-r border-gray-200 bg-white shadow-sm
                  transition-[width] duration-200 ${collapsed ? "w-16" : "w-64"}`}
      aria-label="Sidebar"
    >
      <nav className="h-full flex flex-col">
        <div className="p-4 pb-2 flex items-center">
          <div
            className={`overflow-hidden transition-[width] duration-200
                        ${expanded ? "w-32" : "w-0"}`}
          >
          </div>
        </div>

        <SidebarContext.Provider value={{ expanded }}>
          <ul className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
            {items.map((it) => (
              <SidebarRow key={it.name} {...it} />
            ))}
          </ul>
        </SidebarContext.Provider>

      </nav>
    </aside>
  );
}

function SidebarRow({ icon, name, count, active, alert }: SidebarItemDef) {
  const { expanded } = useContext(SidebarContext);

  return (
    <li
      className={`
        relative group flex items-center pl-2 py-2 px-3 rounded-md cursor-pointer
        transition-colors
        ${active
          ? "bg-gradient-to-tr from-indigo-200 to-indigo-100 text-indigo-800"
          : "hover:bg-indigo-50 text-gray-600"}
      `}
    >
      <div className="w-6 flex justify-center shrink-0">{icon}</div>

      <div
        className={`overflow-hidden transition-[width,margin] duration-200
                    ${expanded ? "w-full ml-3" : "w-0"}`}
      >
        <div className="flex items-center justify-between min-w-0">
          <span className="truncate">{name}</span>

          {typeof count === "number" && (
            <span className="ml-2 shrink-0 text-xs bg-gray-200 rounded-full px-2 py-0.5">
              {count}
            </span>
          )}
        </div>
      </div>

      {alert && (
        <div className={`absolute right-2 w-2 h-2 rounded bg-indigo-400 ${expanded ? "" : "top-2"}`} />
      )}
      {!expanded && (
        <div
          role="tooltip"
          className="absolute left-full ml-6 px-2 py-1 rounded bg-indigo-100 text-indigo-800 text-sm
                     whitespace-nowrap invisible opacity-0 -translate-x-2 transition-all
                     group-hover:visible group-hover:opacity-100 group-hover:translate-x-0"
        >
          {name}{typeof count === "number" ? ` • ${count}` : ""}
        </div>
      )}
    </li>
  );
}
