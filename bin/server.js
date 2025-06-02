#!/usr/bin/env node
import { DocsToolServer } from '../src/server.js';

const server = new DocsToolServer();
server.run().catch(console.error); 