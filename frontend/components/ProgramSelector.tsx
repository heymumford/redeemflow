"use client";

const PROGRAMS = [
  { code: "chase-ur", name: "Chase Ultimate Rewards", color: "bg-blue-500" },
  { code: "amex-mr", name: "Amex Membership Rewards", color: "bg-green-500" },
  { code: "citi-ty", name: "Citi ThankYou", color: "bg-cyan-500" },
  { code: "capital-one", name: "Capital One Miles", color: "bg-red-500" },
  { code: "bilt", name: "Bilt Rewards", color: "bg-purple-500" },
  { code: "wells-fargo", name: "Wells Fargo Rewards", color: "bg-yellow-500" },
  { code: "marriott", name: "Marriott Bonvoy", color: "bg-rose-500" },
  { code: "hilton", name: "Hilton Honors", color: "bg-indigo-500" },
  { code: "ihg", name: "IHG One Rewards", color: "bg-teal-500" },
  { code: "hyatt", name: "World of Hyatt", color: "bg-orange-500" },
];

interface Props {
  selected: string;
  onSelect: (code: string) => void;
}

export default function ProgramSelector({ selected, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {PROGRAMS.map((p) => (
        <button
          key={p.code}
          onClick={() => onSelect(p.code)}
          className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium transition-all ${
            selected === p.code
              ? "bg-rose-600 text-white shadow-sm"
              : "bg-gray-50 text-gray-700 hover:bg-gray-100"
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              selected === p.code ? "bg-white" : p.color
            }`}
          />
          {p.name}
        </button>
      ))}
    </div>
  );
}
