# dotfile

## 环境配置

### Zsh 配置

```bash
# 安装 oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# 安装 zsh 插件
ZSH_CUSTOM="${ZSH:-$HOME/.oh-my-zsh}/custom"
for plugin in zsh-autosuggestions zsh-completions zsh-syntax-highlighting; do
  git clone "https://github.com/zsh-users/${plugin}" "$ZSH_CUSTOM/plugins/${plugin}"
done

# 配置插件
sed -i '/^plugins=(/ s/)$/ zsh-autosuggestions zsh-completions zsh-syntax-highlighting)/' ~/.zshrc

# 安装 starship
curl -sS https://starship.rs/install.sh | sh
echo 'eval "$(starship init zsh)"' >> ~/.zshrc

# 重新加载配置
source ~/.zshrc
```

### 安装字体 Cascadia Nerd

```bash
# 下载字体文件
wget https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/CascadiaCode.zip
wget https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/CascadiaMono.zip

# 创建字体目录并解压
mkdir -p ~/.local/share/fonts
unzip CascadiaCode.zip -d ~/.local/share/fonts/CascadiaCode
unzip CascadiaMono.zip -d ~/.local/share/fonts/CascadiaMono
```
