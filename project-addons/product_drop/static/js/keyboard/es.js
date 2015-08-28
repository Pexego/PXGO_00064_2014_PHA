// Keyboard Language
// please update this section to match this language and email me with corrections!
// es = ISO 639-1 code for Spanish
// ***********************
jQuery.keyboard.language.es = {
	language: 'Spanish',
	display : {
		'a'      : '\u2714:Aceptar (Mayús+Intro)', // check mark - same action as accept
		'accept' : 'Aceptar:Aceptar (Mayús+Intro)',
		'alt'    : 'AltGr:Grafemas alternativos',
		'b'      : '\u2190:Retroceso',    // Left arrow (same as &larr;)
		'bksp'   : 'Retroceso:Retroceso',
		'c'      : '\u2716:Cancelar (Esc)', // big X, close - same action as cancel
		'cancel' : 'Cancelar:Cancelar (Esc)',
		'clear'  : 'C:Vaciar',             // clear num pad
		'combo'  : '\u00f6:Alternar teclas combinadas',
		'dec'    : ',:Decimal',           // decimal point for num pad (optional), change '.' to ',' for European format
		'e'      : '\u21b5:Intro',        // down, then left arrow - enter symbol
		'enter'  : 'Intro:Intro',
		'lock'   : '\u21ea Bloq:Mayús', // caps lock
		's'      : '\u21e7:Mayús',        // thick hollow up arrow
		'shift'  : 'Mayús:Mayús',
		'sign'   : '\u00b1:Cambiar signo',  // +/- sign for num pad
		'space'  : '&nbsp;:Espacio',
		't'      : '\u21e5:Tab',          // right arrow to bar (used since this virtual keyboard works with one directional tabs)
		'tab'    : '\u21e5 Tab:Tab'       // \u21b9 is the true tab symbol (left & right arrows)
	},
	wheelMessage : 'Utilice la rueda del mouse para ver otras teclas'
};
