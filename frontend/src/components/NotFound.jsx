import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => (
  <div style={{ padding: 40, textAlign: 'center' }}>
    <h1 style={{ fontSize: 48, marginBottom: 12 }}>Not Found</h1>
    <p style={{ color: '#ccc' }}>A página solicitada não existe neste site.</p>
    <Link to="/">Voltar para Home</Link>
  </div>
);

export default NotFound;
