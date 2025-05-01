interface ISiteMetadataResult {
  siteTitle: string;
  siteUrl: string;
  description: string;
  logo: string;
  navLinks: {
    name: string;
    url: string;
  }[];
}

const getBasePath = () => {
  const baseUrl = import.meta.env.BASE_URL;
  return baseUrl === '/' ? '' : baseUrl;
};

const data: ISiteMetadataResult = {
  siteTitle: 'Workout Garden',
  siteUrl: 'https://run.yanglele.cc',
  logo: 'https://3aed3bd.webp.li/avatar.png',
  description: 'yanglele workout garden',
  navLinks: [
    {
      name: 'Strava',
      url: "https://www.strava.com/athletes/134921761",
    },
    {
      name: 'Summary',
      url: `${getBasePath()}/summary`,
    },
    {
      name: 'Blog',
      url: 'https://notes.yanglele.cc/',
    },
  ],
};

export default data;
