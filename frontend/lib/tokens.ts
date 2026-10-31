/**
 * Design tokens for Raksha AI Analyst Workspace
 * Matches Palantir-inspired OSINT aesthetic and reference designs.
 */

export const colors = {
  canvas: '#F7F5F0',
  card: '#FFFFFF',
  subtleFill: '#EFECE5',
  border: '#DDD8CC',
  
  text: {
    primary: '#1A1F2B',
    secondary: '#4A5365',
    muted: '#7A8294',
  },
  
  brand: {
    navy: '#1F3A5F',
    navyDark: '#142740',
    saffron: '#C2570C',
    saffronLight: '#FEF3EB',
  },
  
  status: {
    green: '#2F7D4F',
    greenLight: '#EBF7EE',
    amber: '#B7791F',
    amberLight: '#FEF7EC',
    red: '#B42318',
    redLight: '#FEECEB',
    blue: '#2B5FAE',
    blueLight: '#EDF4FC',
  },
  
  rings: {
    1: {
      name: 'India',
      color: '#C2570C',
      bgColor: '#FEF3EB',
      borderColor: '#F8D8C3',
    },
    2: {
      name: 'Adversaries',
      color: '#9B2C2C',
      bgColor: '#FDF2F2',
      borderColor: '#F9D4D4',
    },
    3: {
      name: 'Regional',
      color: '#5B4B8A',
      bgColor: '#F4F2F9',
      borderColor: '#DDD6ED',
    },
    4: {
      name: 'Global',
      color: '#2B5FAE',
      bgColor: '#EDF4FC',
      borderColor: '#CDE1F7',
    },
  },
} as const;

export type RingNumber = 1 | 2 | 3 | 4;
