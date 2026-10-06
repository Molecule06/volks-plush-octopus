// Compatibility renderer. Uses the original Opus mesh, skinning, fur motion,
// picking and tetrahedral simulation without altering the WebGPU renderer.
class WebGLRenderer {
  constructor(canvas, mesh, edges, nParticles) {
    this.canvas = canvas; this.backend = 'WEBGL'; this.mesh = mesh;
    const gl = this.gl = canvas.getContext('webgl2', {antialias: true, alpha: false, powerPreference: 'high-performance'});
    if (!gl) throw new Error('This browser could not start 3D graphics. Try enabling hardware acceleration.');
    this.lost = false; this.w = this.h = 0; this.shells = MOBILE_RENDER ? 0 : 24;
    canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); this.lost = true; this.onLost?.({reason: 'lost', message: 'Graphics were interrupted. Reload to restart.'}); });
    const vertex = `#version 300 es
      precision highp float; precision highp int;
      layout(location=0) in vec3 p; layout(location=1) in vec3 n;
      layout(location=2) in vec3 rest; layout(location=3) in float mat;
      layout(location=4) in vec4 lean; layout(location=5) in vec4 arm;
      uniform mat4 vp; uniform float pile, shells; uniform int mode;
      out vec3 wp, normal, q, tangent; out vec4 ar;
      out float material, height;
      void main(){
        height = mode==1 ? 1.0-float(gl_InstanceID)/shells : 0.0;
        vec3 pos=p;
        if(mode==1) pos += (n*height*inversesqrt(1.0+0.45*dot(lean.xyz,lean.xyz))+lean.xyz*height*height)*pile;
        wp=pos; normal=n; q=rest; ar=arm; material=mat;
        tangent=normalize(n+lean.xyz*2.0*height+vec3(0.00001));
        gl_Position=vp*vec4(pos,1.0);
        gl_Position.z=2.0*gl_Position.z-gl_Position.w;
      }`;
    const common = `precision highp float; precision highp int;
      uniform vec3 eye, key, root, tip, under, cheek, sucker, skin, bg;
      uniform mat4 lightVP; uniform sampler2D shadowMap;
      float hash3(vec3 p){vec3 q=fract(p*0.1031);q+=dot(q,q.yzx+33.33);return fract((q.x+q.y)*q.z);}
      vec3 hash33(vec3 p){vec3 q=fract(p*vec3(0.1031,0.1030,0.0973));q+=dot(q,q.yxz+33.33);return fract((q.xxy+q.yxx)*q.zyx);}
      float ss(float a,float b,float x){float t=clamp((x-a)/(b-a),0.0,1.0);return t*t*(3.0-2.0*t);}
      vec3 outputColor(vec3 c){return pow(max(c,vec3(0.0)),vec3(1.0/2.2));}
      float shadowAt(vec3 P){
        vec4 lp=lightVP*vec4(P,1.0);vec3 v=lp.xyz/lp.w;
        vec2 uv=v.xy*0.5+0.5;
        if(any(lessThan(uv,vec2(0.0)))||any(greaterThan(uv,vec2(1.0))))return 1.0;
        float sh=0.0;vec2 texel=1.0/vec2(textureSize(shadowMap,0));
        for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)
          sh+=step(v.z-0.002,texture(shadowMap,uv+vec2(x,y)*texel*1.6).r);
        return 0.35+0.65*sh/9.0;
      }`;
    const fragment = `#version 300 es
      ${common}
      in vec3 wp,normal,q,tangent; in vec4 ar; in float material,height;
      uniform int mode; uniform float spacing;
      out vec4 color;
      void main(){
        if(mode==3){color=vec4(0.08,0.08,0.09,0.35);return;}
        vec3 N=normalize(normal);if(!gl_FrontFacing)N=-N;
        vec3 V=normalize(eye-wp);vec3 L=key;float sh=shadowAt(wp+N*0.015);
        float diffuse=clamp((dot(N,L)+0.3)/1.3,0.0,1.0);
        vec3 alb=mix(root,tip,0.45+0.55*height);
        float underM=ar.x>=0.0?ss(0.18,0.45,ar.z):0.0;
        alb=mix(alb,under*(0.82+0.18*height),underM);
        float ch=length(vec2((abs(q.x)-0.43)/0.12,(q.y-0.84)/0.075));
        float blush=(1.0-ss(0.3,1.1,ch))*ss(0.2,0.42,q.z)*float(ar.x<0.0);
        alb=mix(alb,cheek,blush);
        float localLength=mix(1.0,0.55,underM);
        if(ar.x>=0.0){
          float s=ar.y,rad=0.068+0.172*pow(max(1.0-s,0.0),1.1);
          float lat=s>0.62?0.0:sign(ar.w)*0.42;
          float stagger=ar.w<0.0&&s<=0.62?0.5:0.0;
          float along=(fract(s*19.0+stagger)-0.5)*1.95/19.0;
          float dr=length(vec2(along,(ar.w-lat)*rad));float rd=0.034*(1.0-0.5*s);
          float on=ss(0.45,0.7,ar.z)*ss(0.08,0.14,s)*(1.0-ss(0.95,0.99,s));
          float disc=(1.0-ss(rd*0.62,rd*0.82,dr))*on;
          float ring=(1.0-ss(0.0,rd*0.22,abs(dr-rd*0.9)))*on;
          alb=mix(alb,sucker,disc);alb=mix(alb,mix(sucker,root,0.6),ring);
          localLength=mix(localLength,0.18,max(disc,ring));
        }
        if(mode==2){
          if(material<1.5){
            vec3 H=normalize(L+V);float shine=pow(max(dot(N,H),0.0),110.0);
            vec3 R=reflect(-V,N);
            float box=ss(0.78,0.9,dot(R,normalize(vec3(-0.55,0.75,0.4))));
            vec3 c=vec3(0.008,0.006,0.005)+vec3(0.7)*shine+vec3(0.32)*box;
            c+=bg*pow(1.0-max(dot(N,V),0.0),5.0)*0.45;
            color=vec4(outputColor(c),1.0);return;
          }
          alb=material>5.5?skin:root*0.12+vec3(0.008);
        }
        float cov=1.0,id=0.5;
        if(mode==1){
          vec3 g=q/spacing,i0=floor(g),f=fract(g),o=mix(vec3(-1.0),vec3(1.0),step(vec3(0.5),f));
          cov=0.0;
          for(int k=0;k<8;k++){
            vec3 cell=i0+vec3(float(k&1),float((k>>1)&1),float((k>>2)&1))*o;
            vec3 r=hash33(cell);float len=(0.62+0.38*fract(r.x*7.13+r.z*3.1))*localLength;
            if(height>len)continue;
            vec3 tilt=(fract(r.zxy*5.31+r.yzx*2.17)-0.5)*(1.5*height);
            float d=length(g-(cell+r+tilt));float radius=0.5*pow(max(1.0-height/len,0.0),0.42);
            float c=1.0-ss(radius*0.25,radius,d);
            if(c>cov){cov=c;id=fract(r.y*13.7+r.x*3.3);}
          }
          if(cov<0.13)discard;
          alb*=0.86+0.28*id;
        }
        float low=mix(0.6,1.0,ss(0.0,0.3,wp.y));
        float ao=mix(0.56,1.0,pow(max(height,0.0),0.7))*low;
        vec3 T=normalize(tangent),tl=T-N*dot(T,N),vt=V-N*dot(V,N);
        float velvet=1.0-0.38*clamp(dot(tl,vt)*1.8,-1.0,1.0);
        vec3 c=alb*(vec3(0.5)*(0.75+0.25*N.y)+vec3(1.16,1.1,1.02)*1.35*diffuse*sh)*ao*velvet;
        float rim=pow(1.0-max(dot(N,V),0.0),2.6)*height*height;
        c+=alb*rim*0.3;
        color=vec4(outputColor(c),mode==1?cov:1.0);
      }`;
    this.program = this.makeProgram(vertex,fragment);
    this.depthProgram = this.makeProgram(`#version 300 es
      precision highp float; precision highp int;layout(location=0)in vec3 p;uniform mat4 vp;
      void main(){gl_Position=vp*vec4(p,1.0);gl_Position.z=2.0*gl_Position.z-gl_Position.w;}`,
      `#version 300 es\nprecision highp float; precision highp int;out vec4 color;void main(){color=vec4(1.0);}`);
    this.floorProgram = this.makeProgram(`#version 300 es
      precision highp float; precision highp int;out vec2 ndc;void main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2))*2.0-1.0;ndc=p;gl_Position=vec4(p,0,1);}`,
      `#version 300 es\n${common}
      in vec2 ndc;uniform mat4 inv;out vec4 color;
      void main(){vec4 a=inv*vec4(ndc,0,1),b=inv*vec4(ndc,1,1);vec3 ro=a.xyz/a.w,rd=normalize(b.xyz/b.w-ro);
        vec3 c=bg; if(rd.y<-0.0001){vec3 P=ro+rd*((-ro.y)/rd.y);float sh=shadowAt(P);
          float contact=exp(-dot(P.xz,P.xz)*1.1)*0.1;c*=sh*(1.0-contact);}
        color=vec4(outputColor(c),1.0);}`);
    this.emptyVAO=gl.createVertexArray();
    this.nV=mesh.rest.length/3;this.dyn=new Float32Array(this.nV*6);this.fur=new Float32Array(this.nV*4);
    this.bodyVAO=this.makeVAO(mesh,this.dyn,this.fur);
    this.edges=edges;this.particleBuf=this.buffer(new Float32Array(nParticles*3),gl.ARRAY_BUFFER,gl.DYNAMIC_DRAW);
    this.lineVAO=gl.createVertexArray();gl.bindVertexArray(this.lineVAO);
    gl.bindBuffer(gl.ARRAY_BUFFER,this.particleBuf);gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,12,0);
    this.buffer(edges,gl.ELEMENT_ARRAY_BUFFER,gl.STATIC_DRAW);gl.bindVertexArray(null);
    this.shadowSize=matchMedia('(pointer:coarse)').matches?512:1024;
    this.shadow=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.shadow);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.DEPTH_COMPONENT24,this.shadowSize,this.shadowSize,0,gl.DEPTH_COMPONENT,gl.UNSIGNED_INT,null);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    this.shadowFBO=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,this.shadowFBO);
    gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,this.shadow,0);
    gl.drawBuffers([gl.NONE]);gl.readBuffer(gl.NONE);
    if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw new Error('Could not create the shadow buffer.');
    gl.bindFramebuffer(gl.FRAMEBUFFER,null);
  }
  makeProgram(v,f){const gl=this.gl,p=gl.createProgram();for(const[type,src]of[[gl.VERTEX_SHADER,v],[gl.FRAGMENT_SHADER,f]]){
    const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));gl.attachShader(p,s);gl.deleteShader(s);}
    gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(p));return p;}
  buffer(data,target,usage){const gl=this.gl,b=gl.createBuffer();gl.bindBuffer(target,b);gl.bufferData(target,data,usage);return b;}
  makeVAO(mesh,dyn,fur){const gl=this.gl,vao=gl.createVertexArray();gl.bindVertexArray(vao);
    const attrib=(loc,size,stride,offset)=>{gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,size,gl.FLOAT,false,stride,offset);};
    const dynBuf=this.buffer(dyn,gl.ARRAY_BUFFER,gl.DYNAMIC_DRAW);attrib(0,3,24,0);attrib(1,3,24,12);
    const n=mesh.rest.length/3,st=new Float32Array(n*8);
    for(let i=0;i<n;i++){st.set(mesh.rest.subarray(i*3,i*3+3),i*8);st[i*8+3]=mesh.mat?mesh.mat[i]:6;
      if(mesh.arm)st.set(mesh.arm.subarray(i*4,i*4+4),i*8+4);else st[i*8+4]=-1;}
    this.buffer(st,gl.ARRAY_BUFFER,gl.STATIC_DRAW);attrib(2,3,32,0);attrib(3,1,32,12);attrib(5,4,32,16);
    const furBuf=this.buffer(fur,gl.ARRAY_BUFFER,gl.DYNAMIC_DRAW);attrib(4,4,16,0);
    this.buffer(mesh.index,gl.ELEMENT_ARRAY_BUFFER,gl.STATIC_DRAW);gl.bindVertexArray(null);
    return{vao,dynBuf,furBuf};}
  setFinger(mesh){this.fingerDyn=new Float32Array(mesh.rest.length*2);this.fingerVAO=this.makeVAO(mesh,this.fingerDyn,new Float32Array(mesh.rest.length/3*4));this.fingerCount=mesh.index.length;this.fingerVisible=false;}
  resize(w,h){this.w=this.canvas.width=Math.max(1,Math.floor(w));this.h=this.canvas.height=Math.max(1,Math.floor(h));}
  setUniforms(cam,light,palette,params){this.cam=cam;this.light=light;this.palette=palette;this.params=params;}
  uploadGeometry(particles,showMesh,moved){const gl=this.gl;const upload=(b,d)=>{gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferSubData(gl.ARRAY_BUFFER,0,d);};
    if(moved)upload(this.bodyVAO.dynBuf,this.dyn);if(!MOBILE_RENDER)upload(this.bodyVAO.furBuf,this.fur);
    if(this.fingerVisible)upload(this.fingerVAO.dynBuf,this.fingerDyn);if(showMesh)upload(this.particleBuf,particles);}
  uniforms(p){const gl=this.gl;gl.useProgram(p);const u=n=>gl.getUniformLocation(p,n);
    gl.uniformMatrix4fv(u('vp'),false,this.cam.viewProj);gl.uniformMatrix4fv(u('inv'),false,this.cam.invViewProj);
    gl.uniformMatrix4fv(u('lightVP'),false,this.light.lightVP);gl.uniform3fv(u('eye'),this.cam.pos);gl.uniform3fv(u('key'),this.light.dir);
    for(const [n,k]of[['root','furRoot'],['tip','furTip'],['under','under'],['cheek','cheek'],['sucker','sucker']])gl.uniform3fv(u(n),this.palette[k]);
    gl.uniform3fv(u('skin'),this.params.skin);gl.uniform3fv(u('bg'),BG_LIN);
    gl.uniform1f(u('pile'),this.params.furLen);gl.uniform1f(u('shells'),this.shells);gl.uniform1f(u('spacing'),this.params.strand);
    gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.shadow);gl.uniform1i(u('shadowMap'),0);}
  draw(showMesh){const gl=this.gl,m=this.mesh;if(this.lost)return;
    gl.bindFramebuffer(gl.FRAMEBUFFER,this.shadowFBO);gl.viewport(0,0,this.shadowSize,this.shadowSize);
    gl.enable(gl.DEPTH_TEST);gl.depthMask(true);gl.disable(gl.BLEND);gl.disable(gl.SAMPLE_ALPHA_TO_COVERAGE);
    // Avoid sampling a texture while it is attached to the active framebuffer.
    gl.bindTexture(gl.TEXTURE_2D,null);gl.clear(gl.DEPTH_BUFFER_BIT);gl.useProgram(this.depthProgram);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.depthProgram,'vp'),false,this.light.lightVP);
    gl.bindVertexArray(this.bodyVAO.vao);gl.drawElements(gl.TRIANGLES,m.body.count+m.props.count,gl.UNSIGNED_INT,0);
    if(this.fingerVisible){gl.bindVertexArray(this.fingerVAO.vao);gl.drawElements(gl.TRIANGLES,this.fingerCount,gl.UNSIGNED_INT,0);}
    gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(0,0,this.w,this.h);gl.clearColor(...BG_SRGB,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.disable(gl.DEPTH_TEST);gl.depthMask(false);this.uniforms(this.floorProgram);gl.bindVertexArray(this.emptyVAO);gl.drawArrays(gl.TRIANGLES,0,3);
    gl.enable(gl.DEPTH_TEST);gl.depthMask(true);this.uniforms(this.program);gl.bindVertexArray(this.bodyVAO.vao);
    const mode=gl.getUniformLocation(this.program,'mode');gl.uniform1i(mode,2);gl.drawElements(gl.TRIANGLES,m.props.count,gl.UNSIGNED_INT,m.props.first*4);
    gl.uniform1i(mode,0);gl.drawElements(gl.TRIANGLES,m.body.count,gl.UNSIGNED_INT,0);
    if(this.fingerVisible){gl.bindVertexArray(this.fingerVAO.vao);gl.uniform1i(mode,2);gl.drawElements(gl.TRIANGLES,this.fingerCount,gl.UNSIGNED_INT,0);gl.bindVertexArray(this.bodyVAO.vao);}
    if(this.shells>0){gl.uniform1i(mode,1);gl.enable(gl.SAMPLE_ALPHA_TO_COVERAGE);gl.drawElementsInstanced(gl.TRIANGLES,m.body.count,gl.UNSIGNED_INT,0,this.shells);gl.disable(gl.SAMPLE_ALPHA_TO_COVERAGE);}
    if(showMesh){gl.bindVertexArray(this.lineVAO);gl.disable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.uniform1i(mode,3);gl.drawElements(gl.LINES,this.edges.length,gl.UNSIGNED_INT,0);gl.disable(gl.BLEND);}
    gl.bindVertexArray(null);
  }
}
