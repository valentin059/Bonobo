// js/data.js — Base de datos de películas y logros

// Array con todas las películas del catálogo de la app
// Cada objeto representa una película con sus datos: id, título, año, puntuación media,
// género, director, reparto, sinopsis e imagen (URLs de Unsplash usadas como placeholder)
const PELICULAS = [
  { id:1,  titulo:"Vengadores: Endgame",           anio:2019, puntuacion:8.4, genero:"Acción",         director:"Hermanos Russo",      reparto:["Robert Downey Jr.","Chris Evans","Scarlett Johansson"], sinopsis:"Los Vengadores restantes se unen para revertir las acciones de Thanos y restaurar el equilibrio del universo, en el cierre épico del UCM.", imagen:"https://images.unsplash.com/photo-1635805737707-575885ab0820?w=400&q=80" },
  { id:2,  titulo:"El Conjuro 3",                  anio:2021, puntuacion:6.3, genero:"Terror",          director:"Michael Chaves",       reparto:["Vera Farmiga","Patrick Wilson"], sinopsis:"Los Warren investigan un caso de posesión demoníaca que lleva a un juicio por asesinato, adentrándose en territorio desconocido.", imagen:"https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=400&q=80" },
  { id:3,  titulo:"La La Land",                    anio:2016, puntuacion:8.0, genero:"Romance",         director:"Damien Chazelle",      reparto:["Ryan Gosling","Emma Stone"], sinopsis:"Una actriz aspirante y un músico de jazz se enamoran en Los Ángeles mientras persiguen sus sueños, entre sacrificios y magia.", imagen:"https://images.unsplash.com/photo-1501854140801-50d01698950b?w=400&q=80" },
  { id:4,  titulo:"Dune: Part Two",                anio:2024, puntuacion:8.5, genero:"Ciencia Ficción", director:"Denis Villeneuve",     reparto:["Timothée Chalamet","Zendaya","Austin Butler"], sinopsis:"Paul Atreides se une a los Fremen en una guerra de venganza mientras navega el peligroso camino hacia convertirse en una figura mesiánica.", imagen:"https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=400&q=80" },
  { id:5,  titulo:"Oppenheimer",                   anio:2023, puntuacion:8.9, genero:"Drama",            director:"Christopher Nolan",    reparto:["Cillian Murphy","Emily Blunt","Matt Damon"], sinopsis:"La historia del físico J. Robert Oppenheimer y su papel en el Proyecto Manhattan, una carrera contra el tiempo que cambió la historia.", imagen:"https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&q=80" },
  { id:6,  titulo:"El Padrino",                    anio:1972, puntuacion:9.2, genero:"Drama",            director:"Francis Ford Coppola", reparto:["Marlon Brando","Al Pacino","James Caan"], sinopsis:"El patriarca de una poderosa familia mafiosa transfiere el control de su imperio criminal a su hijo más joven y reticente.", imagen:"https://images.unsplash.com/photo-1485846234645-a62644f84728?w=400&q=80" },
  { id:7,  titulo:"Parásitos",                     anio:2019, puntuacion:8.5, genero:"Drama",            director:"Bong Joon-ho",         reparto:["Song Kang-ho","Lee Sun-kyun"], sinopsis:"Una familia de clase baja se infiltra hábilmente en la vida de una adinerada familia de Seúl con consecuencias imprevisibles.", imagen:"https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&q=80" },
  { id:8,  titulo:"Coco",                          anio:2017, puntuacion:8.4, genero:"Animación",        director:"Lee Unkrich",          reparto:["Anthony Gonzalez","Gael García Bernal"], sinopsis:"Un niño que sueña con la música viaja accidentalmente a la Tierra de los Muertos durante el Día de Muertos.", imagen:"https://images.unsplash.com/photo-1510511459019-5dda7724fd87?w=400&q=80" },
  { id:9,  titulo:"Interestelar",                  anio:2014, puntuacion:8.7, genero:"Ciencia Ficción",  director:"Christopher Nolan",    reparto:["Matthew McConaughey","Anne Hathaway"], sinopsis:"Un equipo de astronautas viaja a través de un agujero de gusano en busca de un nuevo hogar para la humanidad moribunda.", imagen:"https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=400&q=80" },
  { id:10, titulo:"Blade Runner 2049",             anio:2017, puntuacion:8.0, genero:"Ciencia Ficción",  director:"Denis Villeneuve",     reparto:["Ryan Gosling","Harrison Ford"], sinopsis:"Un blade runner descubre un secreto enterrado durante décadas que tiene el potencial de sumir a la sociedad en el caos.", imagen:"https://images.unsplash.com/photo-1604076850742-4c7221f3101b?w=400&q=80" },
  { id:11, titulo:"Forrest Gump",                  anio:1994, puntuacion:8.8, genero:"Drama",            director:"Robert Zemeckis",      reparto:["Tom Hanks","Robin Wright"], sinopsis:"Un hombre de Alabama con un CI bajo presencia involuntariamente algunos de los eventos históricos más importantes del siglo XX.", imagen:"https://images.unsplash.com/photo-1509347528160-9a9e33742cdb?w=400&q=80" },
  { id:12, titulo:"Mad Max: Furia en el Camino",   anio:2015, puntuacion:8.1, genero:"Acción",           director:"George Miller",        reparto:["Tom Hardy","Charlize Theron"], sinopsis:"En un mundo postapocalíptico, Max se alía con Furiosa para huir de un tirano que controla el agua y liberar a sus esposas.", imagen:"https://images.unsplash.com/photo-1524712245354-2c4e5e7121c0?w=400&q=80" },
  { id:13, titulo:"¿Qué Pasó Ayer?",               anio:2009, puntuacion:7.7, genero:"Comedia",          director:"Todd Phillips",        reparto:["Bradley Cooper","Zach Galifianakis"], sinopsis:"Tres amigos despiertan en una suite de Las Vegas sin recordar nada de la noche anterior y deben reconstruir los hechos.", imagen:"https://images.unsplash.com/photo-1525268323446-0505b6fe7778?w=400&q=80" },
  { id:14, titulo:"Titanic",                       anio:1997, puntuacion:7.9, genero:"Romance",          director:"James Cameron",        reparto:["Leonardo DiCaprio","Kate Winslet"], sinopsis:"Un joven artista y una aristócrata se enamoran a bordo del transatlántico más famoso del mundo, condenado a hundirse.", imagen:"https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=400&q=80" },
  { id:15, titulo:"Spider-Man: Sin Camino a Casa", anio:2021, puntuacion:8.2, genero:"Acción",           director:"Jon Watts",            reparto:["Tom Holland","Zendaya","Benedict Cumberbatch"], sinopsis:"Peter Parker pide al Doctor Strange un hechizo para que nadie sepa que es Spider-Man, pero algo sale terriblemente mal.", imagen:"https://images.unsplash.com/photo-1531259683007-016a7b628fc3?w=400&q=80" },
  { id:16, titulo:"El Gran Lebowski",              anio:1998, puntuacion:8.1, genero:"Comedia",          director:"Joel Coen",            reparto:["Jeff Bridges","John Goodman","Julianne Moore"], sinopsis:"Un holgazán apodado 'El Nota' es confundido con un millonario y se ve envuelto en un absurdo caso de secuestro.", imagen:"https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=400&q=80" },
];

// ── Simulación de Cartelera y Próximos Estrenos ──
// En producción vendrían de TMDB /movie/now_playing y /movie/upcoming
// Son simplemente arrays de IDs que apuntan a películas del array PELICULAS de arriba
const CARTELERA_IDS = [4, 5, 15, 12, 2];   // "en cines ahora"
const ESTRENOS_IDS  = [1, 7, 9, 16, 13];   // "próximamente"

// ── Listas personalizadas (localStorage) ──
// Objeto que gestiona las listas de películas creadas por cada usuario
// Cada usuario tiene sus propias listas guardadas por separado en localStorage
const LISTAS = {
  // Obtiene todas las listas de un usuario. Si no tiene ninguna, devuelve array vacío
  obtenerTodas(nombreUsuario) {
    return JSON.parse(localStorage.getItem('bnb_listas_' + nombreUsuario) || '[]');
  },
  // Guarda el array completo de listas de un usuario en localStorage
  guardar(nombreUsuario, listas) {
    localStorage.setItem('bnb_listas_' + nombreUsuario, JSON.stringify(listas));
  },
  // Crea una nueva lista para el usuario con nombre, descripción, visibilidad y sin películas
  crear(nombreUsuario, nombre, descripcion, esPublica) {
    const listas = this.obtenerTodas(nombreUsuario);
    // Usa Date.now() como ID único (milisegundos actuales, siempre diferente)
    const nueva = { id: Date.now(), nombre, descripcion: descripcion || '', esPublica, peliculas: [], creadaEl: new Date().toISOString() };
    listas.push(nueva);
    this.guardar(nombreUsuario, listas);
    return nueva;
  },
  // Busca y devuelve una lista concreta por su ID, o null si no existe
  obtenerPorId(nombreUsuario, id) {
    return this.obtenerTodas(nombreUsuario).find(l => l.id === id) || null;
  },
  // Actualiza los campos de una lista existente (fusiona los cambios con los datos actuales)
  actualizar(nombreUsuario, id, cambios) {
    const listas = this.obtenerTodas(nombreUsuario).map(l => l.id === id ? { ...l, ...cambios } : l);
    this.guardar(nombreUsuario, listas);
  },
  // Elimina una lista filtrando por ID (todas las listas excepto la que se quiere borrar)
  eliminar(nombreUsuario, id) {
    this.guardar(nombreUsuario, this.obtenerTodas(nombreUsuario).filter(l => l.id !== id));
  },
  // Añade una película a una lista. Devuelve false si la lista no existe o la película ya está
  agregarPelicula(nombreUsuario, idLista, idPelicula) {
    const listas = this.obtenerTodas(nombreUsuario);
    const idx    = listas.findIndex(l => l.id === idLista);
    if (idx < 0) return false;
    // Evita duplicados: si la película ya está en la lista, no la añade
    if (listas[idx].peliculas.includes(idPelicula)) return false;
    listas[idx].peliculas.push(idPelicula);
    this.guardar(nombreUsuario, listas);
    return true;
  },
  // Elimina una película de una lista filtrando el array de películas de esa lista
  quitarPelicula(nombreUsuario, idLista, idPelicula) {
    const listas = this.obtenerTodas(nombreUsuario);
    const idx    = listas.findIndex(l => l.id === idLista);
    if (idx < 0) return false;
    listas[idx].peliculas = listas[idx].peliculas.filter(id => id !== idPelicula);
    this.guardar(nombreUsuario, listas);
    return true;
  },
  // Devuelve solo las listas marcadas como públicas (visibles para otros usuarios)
  obtenerPublicas(nombreUsuario) {
    return this.obtenerTodas(nombreUsuario).filter(l => l.esPublica);
  }
};

// ── CATÁLOGO DE LOGROS ── (según Documento Maestro Bonobo)
// Catálogo completo de logros disponibles en la app, divididos en dos niveles:
// Nivel 1: logros individuales (basados en actividad propia del usuario)
// Nivel 2: logros sociales (basados en interacción con otros usuarios)
// Cada logro tiene: id único, código identificador, nivel, nombre, descripción,
// XP que otorga al reclamarlo e icono emoji
const CATALOGO_LOGROS = [
  // ── NIVEL 1: Visionado / Diario / Perfil ──
  { id:1,  codigo:'primera_vista',      nivel:1, nombre:'Primera Función',       desc:'Marca tu primera película como vista.',              xp:10,  ico:'🎬' },
  { id:2,  codigo:'primera_resena',     nivel:1, nombre:'Crítico Novel',          desc:'Escribe tu primera reseña en el diario.',            xp:20,  ico:'✍️' },
  { id:3,  codigo:'cinco_vistas',       nivel:1, nombre:'Cinéfilo',               desc:'Marca 5 películas como vistas.',                     xp:30,  ico:'🍿' },
  { id:4,  codigo:'diez_vistas',        nivel:1, nombre:'Cinéfilo en Progreso',   desc:'Marca 10 películas como vistas.',                    xp:50,  ico:'🏃' },
  { id:5,  codigo:'maratonista',        nivel:1, nombre:'Maratonista',            desc:'Registra 10 películas en un mismo mes.',             xp:50,  ico:'🎯' },
  { id:6,  codigo:'primera_fav',        nivel:1, nombre:'Con Criterio',           desc:'Añade tu primera película a favoritas.',             xp:15,  ico:'⭐' },
  { id:7,  codigo:'watchlist_5',        nivel:1, nombre:'Planificador',           desc:'Añade 5 películas a tu watchlist.',                  xp:25,  ico:'📋' },
  { id:8,  codigo:'tres_resenas',       nivel:1, nombre:'Periodista',             desc:'Escribe 3 reseñas en el diario.',                    xp:35,  ico:'📰' },
  { id:9,  codigo:'cuatro_generos',     nivel:1, nombre:'Omnívoro',               desc:'Ve películas de 4 géneros distintos.',               xp:40,  ico:'🌍' },
  // ── NIVEL 2: Sociales ──
  { id:10, codigo:'primer_seguido',     nivel:2, nombre:'Sociable',               desc:'Sigue a tu primer usuario.',                         xp:20,  ico:'👥' },
  { id:11, codigo:'primer_like_resena', nivel:2, nombre:'Apreciador',             desc:'Da tu primer like a la reseña de otro usuario.',     xp:15,  ico:'❤️' },
  { id:12, codigo:'primer_comentario',  nivel:2, nombre:'Conversador',            desc:'Comenta en la reseña de otro usuario por 1ª vez.',   xp:15,  ico:'💬' },
  { id:13, codigo:'diez_seguidores',    nivel:2, nombre:'Influencer',             desc:'Consigue 10 seguidores.',                            xp:60,  ico:'🌟' },
];