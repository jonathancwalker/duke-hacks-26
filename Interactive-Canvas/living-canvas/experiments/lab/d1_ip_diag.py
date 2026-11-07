# Diagnostic: is the IP-Adapter actually wired? Compare my packed embeds vs the pipeline's own encoding.
nm = "Van Gogh, The Starry Night (1889)"
v = ART_V[nm]
pe = xl.prepare_ip_adapter_image_embeds([ART[nm]], None, DEV, 1, False)
print("pipeline embeds:", [tuple(t.shape) for t in pe], "max diff vs mine:", float((pe[0].float().reshape(-1) - v.reshape(-1)).abs().max()))
print("unet ip processors:", sum("IPAdapter" in type(p).__name__ for p in xl.unet.attn_processors.values()))
a = render(ip=v, ip_scale=1.0)
b = render(ip=v, ip_scale=1.0, cn_scale=0.0)
xl.set_ip_adapter_scale(1.0)
c = xl(prompt_embeds=S_PE, pooled_prompt_embeds=S_PP, ip_adapter_image=ART[nm], image=EDGES, controlnet_conditioning_scale=0.0,
       num_inference_steps=4, guidance_scale=0.0, width=W, height=H, generator=gen()).images[0]
d = render(cond=E(""), ip=v, ip_scale=1.0, cn_scale=0.0)
show(board([[ART[nm], a, b, c, d]], ["diag"], ["reference", "mine, ip 1.0, cn .45", "mine, ip 1.0, cn 0", "pipeline-encoded, ip 1.0, cn 0", "empty prompt, ip 1.0, cn 0"]), "D1_ip_diag")
